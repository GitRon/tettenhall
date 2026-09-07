import pytest

from apps.common.domain.dice import DiceNotation, DiceRoll
from apps.skirmish.choices.blow_outcome import BlowOutcomeChoices
from apps.skirmish.choices.skirmish_action import SkirmishActionChoices
from apps.skirmish.domain.action_roll import ActionRoll
from apps.skirmish.handlers.events.warrior import (
    handle_capture_unconscious_warriors,
    handle_experience_gain_after_battle_for_victor,
    handle_experience_gain_on_warrior_incapacitation,
    handle_morale_change_on_resolved_blow,
    handle_morale_drop_on_faction_on_warrior_is_out_of_fight,
    handle_reduce_health_and_update_condition,
    handle_stat_growth_on_warrior_level_up,
)
from apps.skirmish.messages.commands.warrior import (
    CaptureWarrior,
    IncreaseExperience,
    IncreaseMorale,
    IncreaseWarriorStatsOnLevelUp,
    ReduceHealth,
    ReduceMorale,
    ReduceMoraleOfRemainingWarriors,
)
from apps.skirmish.messages.events.skirmish import SkirmishFinished
from apps.skirmish.messages.events.warrior import (
    WarriorDefendedAllDamage,
    WarriorGainedLevel,
    WarriorHasFled,
    WarriorTookDamage,
    WarriorWasIncapacitated,
    WarriorWasKilled,
)
from apps.skirmish.tests.factories.skirmish import SkirmishFactory
from apps.skirmish.tests.factories.warrior import WarriorFactory


def test_handle_reduce_health_and_update_condition_costs_the_defender_health():
    skirmish = SkirmishFactory.build()
    attacker = WarriorFactory.build()
    defender = WarriorFactory.build()

    result = handle_reduce_health_and_update_condition(
        context=WarriorTookDamage(
            skirmish=skirmish,
            round_number=1,
            attacker=attacker,
            attacker_action=SkirmishActionChoices.SIMPLE_ATTACK,
            attack=ActionRoll(roll=DiceRoll(notation=DiceNotation(dice_string="2d6"), result=7), value=7),
            defender=defender,
            defender_action=SkirmishActionChoices.SIMPLE_ATTACK,
            defense=ActionRoll(roll=DiceRoll(notation=DiceNotation(dice_string="1d4"), result=2), value=2),
            damage=5,
        )
    )

    assert result == ReduceHealth(skirmish=skirmish, warrior=defender, attacker=attacker, lost_health=5)


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


def test_handle_stat_growth_on_warrior_level_up_asks_for_the_growth():
    skirmish = SkirmishFactory.build()
    warrior = WarriorFactory.build(faction=skirmish.attacking_faction)

    result = handle_stat_growth_on_warrior_level_up(
        context=WarriorGainedLevel(skirmish=skirmish, warrior=warrior, level=2)
    )

    assert result == IncreaseWarriorStatsOnLevelUp(skirmish=skirmish, warrior=warrior)


@pytest.mark.django_db
def test_handle_morale_change_on_resolved_blow_rewards_a_blow_turned_aside():
    """
    The case the whole rule is for: a defender who out-rolls a real blow is steadied, even though the
    damage floor let a quarter of it past him.
    """
    skirmish = SkirmishFactory()
    attacker = WarriorFactory(faction=skirmish.attacking_faction)
    defender = WarriorFactory(faction=skirmish.defending_faction, current_morale=10, max_morale=20)

    result = handle_morale_change_on_resolved_blow(
        context=WarriorTookDamage(
            skirmish=skirmish,
            round_number=1,
            attacker=attacker,
            attacker_action=SkirmishActionChoices.SIMPLE_ATTACK,
            attack=ActionRoll(roll=DiceRoll(notation=DiceNotation(dice_string="2d6"), result=6), value=6),
            defender=defender,
            defender_action=SkirmishActionChoices.SIMPLE_ATTACK,
            defense=ActionRoll(roll=DiceRoll(notation=DiceNotation(dice_string="2d6"), result=8), value=8),
            damage=2,
        )
    )

    assert result == IncreaseMorale(skirmish=skirmish, warrior=defender, increased_morale=2)


@pytest.mark.django_db
def test_handle_morale_change_on_resolved_blow_shakes_a_beaten_guard():
    skirmish = SkirmishFactory()
    attacker = WarriorFactory(faction=skirmish.attacking_faction)
    defender = WarriorFactory(faction=skirmish.defending_faction, current_morale=10, max_morale=20)

    result = handle_morale_change_on_resolved_blow(
        context=WarriorTookDamage(
            skirmish=skirmish,
            round_number=1,
            attacker=attacker,
            attacker_action=SkirmishActionChoices.SIMPLE_ATTACK,
            attack=ActionRoll(roll=DiceRoll(notation=DiceNotation(dice_string="2d6"), result=9), value=9),
            defender=defender,
            defender_action=SkirmishActionChoices.SIMPLE_ATTACK,
            defense=ActionRoll(roll=DiceRoll(notation=DiceNotation(dice_string="1d4"), result=3), value=3),
            damage=6,
        )
    )

    assert result == ReduceMorale(skirmish=skirmish, warrior=defender, lost_morale=2)


@pytest.mark.django_db
def test_handle_morale_change_on_resolved_blow_rewards_a_fully_absorbed_blow_once():
    """
    An attack of two or less is the only one armour can swallow whole, and it pays the same tenth as
    any other block rather than a second helping on top of it.
    """
    skirmish = SkirmishFactory()
    attacker = WarriorFactory(faction=skirmish.attacking_faction)
    defender = WarriorFactory(faction=skirmish.defending_faction, current_morale=10, max_morale=20)

    result = handle_morale_change_on_resolved_blow(
        context=WarriorDefendedAllDamage(
            skirmish=skirmish,
            round_number=1,
            attacker=attacker,
            attacker_action=SkirmishActionChoices.SIMPLE_ATTACK,
            attack=ActionRoll(roll=DiceRoll(notation=DiceNotation(dice_string="2d6"), result=2), value=2),
            defender=defender,
            defender_action=SkirmishActionChoices.SIMPLE_ATTACK,
            defense=ActionRoll(roll=DiceRoll(notation=DiceNotation(dice_string="2d6"), result=5), value=5),
            outcome=BlowOutcomeChoices.OUTCOME_ABSORBED,
        )
    )

    assert result == IncreaseMorale(skirmish=skirmish, warrior=defender, increased_morale=2)


@pytest.mark.django_db
def test_handle_morale_change_on_resolved_blow_pays_nothing_for_a_swing_that_went_wide():
    """
    A risky attack that missed rolls no die and throws no blow, so there was nothing for the defender
    to turn aside and nothing his nerve should be credited with.
    """
    skirmish = SkirmishFactory()
    attacker = WarriorFactory(faction=skirmish.attacking_faction)
    defender = WarriorFactory(faction=skirmish.defending_faction, current_morale=10, max_morale=20)

    result = handle_morale_change_on_resolved_blow(
        context=WarriorDefendedAllDamage(
            skirmish=skirmish,
            round_number=1,
            attacker=attacker,
            attacker_action=SkirmishActionChoices.RISKY_ATTACK,
            attack=ActionRoll(roll=None, value=0, outcome=BlowOutcomeChoices.OUTCOME_MISSED),
            defender=defender,
            defender_action=SkirmishActionChoices.SIMPLE_ATTACK,
            defense=ActionRoll(roll=DiceRoll(notation=DiceNotation(dice_string="2d6"), result=5), value=5),
            outcome=BlowOutcomeChoices.OUTCOME_MISSED,
        )
    )

    assert result is None


@pytest.mark.django_db
def test_handle_morale_change_on_resolved_blow_rewards_nothing_on_a_tiny_morale_pool():
    """
    The floor below applies to the drain only. A tenth of a small pool rounds to nothing on the reward
    side - a warrior too brittle to earn a point of morale is not handed one.
    """
    skirmish = SkirmishFactory()
    attacker = WarriorFactory(faction=skirmish.attacking_faction)
    defender = WarriorFactory(faction=skirmish.defending_faction, current_morale=4, max_morale=4)

    result = handle_morale_change_on_resolved_blow(
        context=WarriorTookDamage(
            skirmish=skirmish,
            round_number=1,
            attacker=attacker,
            attacker_action=SkirmishActionChoices.SIMPLE_ATTACK,
            attack=ActionRoll(roll=DiceRoll(notation=DiceNotation(dice_string="2d6"), result=6), value=6),
            defender=defender,
            defender_action=SkirmishActionChoices.SIMPLE_ATTACK,
            defense=ActionRoll(roll=DiceRoll(notation=DiceNotation(dice_string="2d6"), result=8), value=8),
            damage=2,
        )
    )

    assert result is None


@pytest.mark.django_db
def test_handle_morale_change_on_resolved_blow_wears_down_a_turtle():
    """
    Standing behind a shield is what makes a fight unwinnable, so it costs nerve instead of building
    it - whatever the attacker managed to put through.
    """
    skirmish = SkirmishFactory()
    attacker = WarriorFactory(faction=skirmish.attacking_faction)
    defender = WarriorFactory(faction=skirmish.defending_faction, current_morale=10, max_morale=20)

    result = handle_morale_change_on_resolved_blow(
        context=WarriorTookDamage(
            skirmish=skirmish,
            round_number=1,
            attacker=attacker,
            attacker_action=SkirmishActionChoices.SIMPLE_ATTACK,
            attack=ActionRoll(roll=DiceRoll(notation=DiceNotation(dice_string="2d6"), result=12), value=12),
            defender=defender,
            defender_action=SkirmishActionChoices.DEFENSIVE_STANCE,
            defense=ActionRoll(roll=DiceRoll(notation=DiceNotation(dice_string="1d4"), result=4), value=8),
            damage=4,
        )
    )

    assert result == ReduceMorale(skirmish=skirmish, warrior=defender, lost_morale=2)


@pytest.mark.django_db
def test_handle_morale_change_on_resolved_blow_always_costs_a_turtle_at_least_a_point():
    """
    A tenth of a small morale pool rounds to nothing, and a stance that costs nothing is the
    unwinnable fight all over again - so the drain reaches a warrior nobody is even swinging at.
    """
    skirmish = SkirmishFactory()
    attacker = WarriorFactory(faction=skirmish.attacking_faction)
    defender = WarriorFactory(faction=skirmish.defending_faction, current_morale=4, max_morale=4)

    result = handle_morale_change_on_resolved_blow(
        context=WarriorDefendedAllDamage(
            skirmish=skirmish,
            round_number=1,
            attacker=attacker,
            attacker_action=SkirmishActionChoices.DEFENSIVE_STANCE,
            attack=ActionRoll(roll=None, value=0, outcome=BlowOutcomeChoices.OUTCOME_NOT_THROWN),
            defender=defender,
            defender_action=SkirmishActionChoices.DEFENSIVE_STANCE,
            defense=ActionRoll(roll=DiceRoll(notation=DiceNotation(dice_string="1d4"), result=4), value=8),
            outcome=BlowOutcomeChoices.OUTCOME_NOT_THROWN,
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
