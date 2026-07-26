import pytest

from apps.skirmish.handlers.events.warrior import (
    handle_capture_unconscious_warriors,
    handle_experience_gain_after_battle_for_victor,
    handle_morale_drop_on_faction_on_warrior_is_out_of_fight,
    handle_morale_increase_on_warriors_defends_all_damage,
)
from apps.skirmish.messages.commands.warrior import (
    CaptureWarrior,
    IncreaseExperience,
    IncreaseMorale,
    ReduceMorale,
)
from apps.skirmish.messages.events.skirmish import SkirmishFinished
from apps.skirmish.messages.events.warrior import (
    WarriorDefendedAllDamage,
    WarriorHasFled,
    WarriorWasIncapacitated,
    WarriorWasKilled,
)
from apps.skirmish.tests.factories.skirmish import SkirmishFactory
from apps.skirmish.tests.factories.warrior import WarriorFactory


@pytest.mark.django_db
def test_handle_morale_drop_on_faction_on_warrior_is_out_of_fight_hits_the_comrades_of_a_fleeing_warrior():
    skirmish = SkirmishFactory()
    fleeing_warrior = WarriorFactory(faction=skirmish.player_faction, max_morale=20)
    comrade = WarriorFactory(faction=skirmish.player_faction)
    skirmish.player_warriors.add(fleeing_warrior, comrade)

    result = handle_morale_drop_on_faction_on_warrior_is_out_of_fight(
        context=WarriorHasFled(skirmish=skirmish, warrior=fleeing_warrior)
    )

    assert result == [ReduceMorale(skirmish=skirmish, warrior=comrade, lost_morale=2)]


@pytest.mark.django_db
def test_handle_morale_drop_on_faction_on_warrior_is_out_of_fight_hits_the_comrades_of_an_incapacitated_enemy():
    skirmish = SkirmishFactory()
    incapacitated_warrior = WarriorFactory(faction=skirmish.non_player_faction, max_morale=20)
    comrade = WarriorFactory(faction=skirmish.non_player_faction)
    attacker = WarriorFactory(faction=skirmish.player_faction)
    skirmish.non_player_warriors.add(incapacitated_warrior, comrade)

    result = handle_morale_drop_on_faction_on_warrior_is_out_of_fight(
        context=WarriorWasIncapacitated(skirmish=skirmish, warrior=incapacitated_warrior, by_warrior=attacker)
    )

    assert result == [ReduceMorale(skirmish=skirmish, warrior=comrade, lost_morale=2)]


@pytest.mark.django_db
def test_handle_morale_drop_on_faction_on_warrior_is_out_of_fight_skips_the_killed_warrior_himself():
    skirmish = SkirmishFactory()
    killed_warrior = WarriorFactory(faction=skirmish.player_faction, max_morale=20)
    killer = WarriorFactory(faction=skirmish.non_player_faction)
    skirmish.player_warriors.add(killed_warrior)

    result = handle_morale_drop_on_faction_on_warrior_is_out_of_fight(
        context=WarriorWasKilled(skirmish=skirmish, warrior=killed_warrior, by_warrior=killer)
    )

    assert result == []


@pytest.mark.django_db
def test_handle_morale_increase_on_warriors_defends_all_damage_rewards_the_defender():
    skirmish = SkirmishFactory()
    attacker = WarriorFactory(faction=skirmish.player_faction)
    defender = WarriorFactory(faction=skirmish.non_player_faction, current_morale=10, max_morale=20)

    result = handle_morale_increase_on_warriors_defends_all_damage(
        context=WarriorDefendedAllDamage(
            skirmish=skirmish,
            attacker=attacker,
            attacker_damage=5,
            defender=defender,
            defender_damage=5,
        )
    )

    assert result == IncreaseMorale(skirmish=skirmish, warrior=defender, increased_morale=2)


@pytest.mark.django_db
def test_handle_morale_increase_on_warriors_defends_all_damage_rewards_nothing_on_a_tiny_morale_pool():
    skirmish = SkirmishFactory()
    attacker = WarriorFactory(faction=skirmish.player_faction)
    defender = WarriorFactory(faction=skirmish.non_player_faction, current_morale=4, max_morale=4)

    result = handle_morale_increase_on_warriors_defends_all_damage(
        context=WarriorDefendedAllDamage(
            skirmish=skirmish,
            attacker=attacker,
            attacker_damage=5,
            defender=defender,
            defender_damage=5,
        )
    )

    assert result is None


@pytest.mark.django_db
def test_handle_capture_unconscious_warriors_captures_every_defeated_warrior():
    skirmish = SkirmishFactory()
    skirmish.victorious_faction = skirmish.player_faction
    skirmish.save()
    unconscious_enemy_warrior = WarriorFactory(faction=skirmish.non_player_faction)

    result = handle_capture_unconscious_warriors(
        context=SkirmishFinished(
            skirmish=skirmish,
            incapacitated_warriors=[],
            defeated_unconscious_warriors=[unconscious_enemy_warrior],
            victorious_conscious_warriors=[],
            quest_name="Raid",
            quest_loot=250,
            month=3,
        )
    )

    assert result == [
        CaptureWarrior(
            skirmish=skirmish,
            warrior=unconscious_enemy_warrior,
            capturing_faction=skirmish.player_faction,
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
            victorious_conscious_warriors=[],
            quest_name="Raid",
            quest_loot=250,
            month=3,
        )
    )

    assert result == []


@pytest.mark.django_db
def test_handle_experience_gain_after_battle_for_victor_rewards_every_surviving_warrior():
    skirmish = SkirmishFactory()
    healthy_player_warrior = WarriorFactory(faction=skirmish.player_faction)

    result = handle_experience_gain_after_battle_for_victor(
        context=SkirmishFinished(
            skirmish=skirmish,
            incapacitated_warriors=[],
            defeated_unconscious_warriors=[],
            victorious_conscious_warriors=[healthy_player_warrior],
            quest_name="Raid",
            quest_loot=250,
            month=3,
        )
    )

    assert result == [IncreaseExperience(skirmish=skirmish, warrior=healthy_player_warrior, increased_experience=10)]


@pytest.mark.django_db
def test_handle_experience_gain_after_battle_for_victor_rewards_nobody_without_survivors():
    skirmish = SkirmishFactory()

    result = handle_experience_gain_after_battle_for_victor(
        context=SkirmishFinished(
            skirmish=skirmish,
            incapacitated_warriors=[],
            defeated_unconscious_warriors=[],
            victorious_conscious_warriors=[],
            quest_name="Raid",
            quest_loot=250,
            month=3,
        )
    )

    assert result == []
