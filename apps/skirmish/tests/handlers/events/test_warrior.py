import pytest

from apps.skirmish.choices.skirmish_action import SkirmishActionChoices
from apps.skirmish.handlers.events.warrior import (
    handle_capture_unconscious_warriors,
    handle_experience_gain_after_battle_for_victor,
    handle_experience_gain_on_warrior_incapacitation,
    handle_morale_change_on_warrior_defends_all_damage,
    handle_morale_drop_on_faction_on_warrior_is_out_of_fight,
    handle_reduce_health_and_update_condition,
)
from apps.skirmish.messages.commands.warrior import (
    CaptureWarrior,
    IncreaseExperience,
    IncreaseMorale,
    ReduceHealth,
    ReduceMorale,
    ReduceMoraleOfRemainingWarriors,
)
from apps.skirmish.messages.events.skirmish import SkirmishFinished
from apps.skirmish.messages.events.warrior import (
    WarriorDefendedAllDamage,
    WarriorHasFled,
    WarriorTookDamage,
    WarriorWasIncapacitated,
    WarriorWasKilled,
)
from apps.skirmish.tests.factories.skirmish import SkirmishFactory
from apps.skirmish.tests.factories.warrior import WarriorFactory


def test_handle_reduce_health_and_update_condition_costs_the_defender_health_and_morale():
    skirmish = SkirmishFactory.build()
    attacker = WarriorFactory.build()
    defender = WarriorFactory.build(max_morale=20)

    result = handle_reduce_health_and_update_condition(
        context=WarriorTookDamage(
            skirmish=skirmish,
            attacker=attacker,
            attacker_damage=7,
            defender=defender,
            defender_damage=2,
            damage=5,
        )
    )

    assert result == [
        ReduceHealth(skirmish=skirmish, warrior=defender, attacker=attacker, lost_health=5),
        ReduceMorale(skirmish=skirmish, warrior=defender, lost_morale=2),
    ]


def test_handle_morale_drop_on_faction_on_warrior_is_out_of_fight_for_a_fleeing_warrior():
    """
    One test per registered message: the handler is registered for three of them, and the mapping
    is all it does - the participants get read in the command handler, since strict mode blocks
    database access here.
    """
    skirmish = SkirmishFactory.build()
    fleeing_warrior = WarriorFactory.build(faction=skirmish.attacking_faction)

    result = handle_morale_drop_on_faction_on_warrior_is_out_of_fight(
        context=WarriorHasFled(skirmish=skirmish, warrior=fleeing_warrior)
    )

    assert result == ReduceMoraleOfRemainingWarriors(skirmish=skirmish, warrior=fleeing_warrior)


def test_handle_morale_drop_on_faction_on_warrior_is_out_of_fight_for_an_incapacitated_warrior():
    skirmish = SkirmishFactory.build()
    incapacitated_warrior = WarriorFactory.build(faction=skirmish.defending_faction)
    attacker = WarriorFactory.build(faction=skirmish.attacking_faction)

    result = handle_morale_drop_on_faction_on_warrior_is_out_of_fight(
        context=WarriorWasIncapacitated(skirmish=skirmish, warrior=incapacitated_warrior, by_warrior=attacker)
    )

    assert result == ReduceMoraleOfRemainingWarriors(skirmish=skirmish, warrior=incapacitated_warrior)


def test_handle_morale_drop_on_faction_on_warrior_is_out_of_fight_for_a_killed_warrior():
    skirmish = SkirmishFactory.build()
    killed_warrior = WarriorFactory.build(faction=skirmish.attacking_faction)
    killer = WarriorFactory.build(faction=skirmish.defending_faction)

    result = handle_morale_drop_on_faction_on_warrior_is_out_of_fight(
        context=WarriorWasKilled(skirmish=skirmish, warrior=killed_warrior, by_warrior=killer)
    )

    assert result == ReduceMoraleOfRemainingWarriors(skirmish=skirmish, warrior=killed_warrior)


def test_handle_experience_gain_on_warrior_incapacitation_for_an_incapacitated_warrior():
    """
    One test per registered message: the handler is registered for two of them.
    """
    skirmish = SkirmishFactory.build()
    incapacitated_warrior = WarriorFactory.build(faction=skirmish.defending_faction)
    attacker = WarriorFactory.build(faction=skirmish.attacking_faction)

    result = handle_experience_gain_on_warrior_incapacitation(
        context=WarriorWasIncapacitated(skirmish=skirmish, warrior=incapacitated_warrior, by_warrior=attacker)
    )

    assert result == IncreaseExperience(skirmish=skirmish, warrior=attacker, increased_experience=25)


def test_handle_experience_gain_on_warrior_incapacitation_for_a_killed_warrior():
    skirmish = SkirmishFactory.build()
    killed_warrior = WarriorFactory.build(faction=skirmish.defending_faction)
    killer = WarriorFactory.build(faction=skirmish.attacking_faction)

    result = handle_experience_gain_on_warrior_incapacitation(
        context=WarriorWasKilled(skirmish=skirmish, warrior=killed_warrior, by_warrior=killer)
    )

    assert result == IncreaseExperience(skirmish=skirmish, warrior=killer, increased_experience=25)


@pytest.mark.django_db
def test_handle_morale_change_on_warrior_defends_all_damage_rewards_a_real_defence():
    skirmish = SkirmishFactory()
    attacker = WarriorFactory(faction=skirmish.attacking_faction)
    defender = WarriorFactory(faction=skirmish.defending_faction, current_morale=10, max_morale=20)

    result = handle_morale_change_on_warrior_defends_all_damage(
        context=WarriorDefendedAllDamage(
            skirmish=skirmish,
            attacker=attacker,
            attacker_damage=5,
            defender=defender,
            defender_damage=5,
            defender_action=SkirmishActionChoices.SIMPLE_ATTACK,
        )
    )

    assert result == IncreaseMorale(skirmish=skirmish, warrior=defender, increased_morale=2)


@pytest.mark.django_db
def test_handle_morale_change_on_warrior_defends_all_damage_wears_down_a_turtle():
    """
    Standing behind a shield is what makes a fight unwinnable, so it costs nerve instead of building
    it - otherwise nothing moves the morale of a warrior nobody can hurt.
    """
    skirmish = SkirmishFactory()
    attacker = WarriorFactory(faction=skirmish.attacking_faction)
    defender = WarriorFactory(faction=skirmish.defending_faction, current_morale=10, max_morale=20)

    result = handle_morale_change_on_warrior_defends_all_damage(
        context=WarriorDefendedAllDamage(
            skirmish=skirmish,
            attacker=attacker,
            attacker_damage=5,
            defender=defender,
            defender_damage=5,
            defender_action=SkirmishActionChoices.DEFENSIVE_STANCE,
        )
    )

    assert result == ReduceMorale(skirmish=skirmish, warrior=defender, lost_morale=2)


@pytest.mark.django_db
def test_handle_morale_change_on_warrior_defends_all_damage_rewards_nothing_on_a_tiny_morale_pool():
    """
    The floor below applies to the drain only. A tenth of a small pool still rounds to nothing on the
    reward side, exactly as it did before there was a drain at all - a warrior too brittle to earn a
    point of morale is not handed one.
    """
    skirmish = SkirmishFactory()
    attacker = WarriorFactory(faction=skirmish.attacking_faction)
    defender = WarriorFactory(faction=skirmish.defending_faction, current_morale=4, max_morale=4)

    result = handle_morale_change_on_warrior_defends_all_damage(
        context=WarriorDefendedAllDamage(
            skirmish=skirmish,
            attacker=attacker,
            attacker_damage=5,
            defender=defender,
            defender_damage=5,
            defender_action=SkirmishActionChoices.SIMPLE_ATTACK,
        )
    )

    assert result is None


@pytest.mark.django_db
def test_handle_morale_change_on_warrior_defends_all_damage_always_costs_at_least_a_point():
    """
    A tenth of a small morale pool rounds to nothing, and a stance that costs nothing is the
    unwinnable fight all over again.
    """
    skirmish = SkirmishFactory()
    attacker = WarriorFactory(faction=skirmish.attacking_faction)
    defender = WarriorFactory(faction=skirmish.defending_faction, current_morale=4, max_morale=4)

    result = handle_morale_change_on_warrior_defends_all_damage(
        context=WarriorDefendedAllDamage(
            skirmish=skirmish,
            attacker=attacker,
            attacker_damage=5,
            defender=defender,
            defender_damage=5,
            defender_action=SkirmishActionChoices.DEFENSIVE_STANCE,
        )
    )

    assert result == ReduceMorale(skirmish=skirmish, warrior=defender, lost_morale=1)


@pytest.mark.django_db
def test_handle_capture_unconscious_warriors_captures_every_defeated_warrior():
    skirmish = SkirmishFactory()
    skirmish.victorious_faction = skirmish.attacking_faction
    skirmish.save()
    unconscious_enemy_warrior = WarriorFactory(faction=skirmish.defending_faction)

    result = handle_capture_unconscious_warriors(
        context=SkirmishFinished(
            skirmish=skirmish,
            incapacitated_warriors=[],
            defeated_unconscious_warriors=[unconscious_enemy_warrior],
            victorious_healthy_warriors=[],
            quest_name="Raid",
            quest_loot=250,
            month=3,
        )
    )

    assert result == [
        CaptureWarrior(
            skirmish=skirmish,
            warrior=unconscious_enemy_warrior,
            capturing_faction=skirmish.attacking_faction,
        )
    ]


@pytest.mark.django_db
def test_handle_capture_unconscious_warriors_captures_nobody_without_defeated_warriors():
    skirmish = SkirmishFactory()

    result = handle_capture_unconscious_warriors(
        context=SkirmishFinished(
            skirmish=skirmish,
            incapacitated_warriors=[],
            defeated_unconscious_warriors=[],
            victorious_healthy_warriors=[],
            quest_name="Raid",
            quest_loot=250,
            month=3,
        )
    )

    assert result == []


@pytest.mark.django_db
def test_handle_experience_gain_after_battle_for_victor_rewards_every_surviving_warrior():
    skirmish = SkirmishFactory()
    healthy_attacking_warrior = WarriorFactory(faction=skirmish.attacking_faction)

    result = handle_experience_gain_after_battle_for_victor(
        context=SkirmishFinished(
            skirmish=skirmish,
            incapacitated_warriors=[],
            defeated_unconscious_warriors=[],
            victorious_healthy_warriors=[healthy_attacking_warrior],
            quest_name="Raid",
            quest_loot=250,
            month=3,
        )
    )

    assert result == [IncreaseExperience(skirmish=skirmish, warrior=healthy_attacking_warrior, increased_experience=10)]


@pytest.mark.django_db
def test_handle_experience_gain_after_battle_for_victor_rewards_nobody_without_survivors():
    skirmish = SkirmishFactory()

    result = handle_experience_gain_after_battle_for_victor(
        context=SkirmishFinished(
            skirmish=skirmish,
            incapacitated_warriors=[],
            defeated_unconscious_warriors=[],
            victorious_healthy_warriors=[],
            quest_name="Raid",
            quest_loot=250,
            month=3,
        )
    )

    assert result == []
