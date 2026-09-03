from apps.faction.tests.factories.faction import FactionFactory
from apps.item.tests.factories.item import ItemFactory
from apps.skirmish.choices.skirmish_action import SkirmishActionChoices
from apps.skirmish.handlers.events.battle_history import (
    handle_log_attacker_defender_decided,
    handle_log_item_dropped,
    handle_log_round_finished,
    handle_log_skirmish_finished,
    handle_log_warrior_death,
    handle_log_warrior_defends_all_damage,
    handle_log_warrior_incapacitation,
    handle_log_warrior_takes_damage,
    handle_warrior_dropped_silver,
    handle_warrior_gained_experience,
    handle_warrior_gained_level,
    handle_warrior_gains_morale,
    handle_warrior_has_fled,
    handle_warrior_improved_stats,
    handle_warrior_is_captured,
    handle_warrior_lost_morale,
)
from apps.skirmish.messages.commands.battle_history import CreateBattleHistory
from apps.skirmish.messages.events.item import ItemDroppedAsLoot
from apps.skirmish.messages.events.skirmish import AttackerDefenderDecided, RoundFinished, SkirmishFinished
from apps.skirmish.messages.events.transaction import WarriorDroppedSilver
from apps.skirmish.messages.events.warrior import (
    WarriorDefendedAllDamage,
    WarriorGainedExperience,
    WarriorGainedLevel,
    WarriorGainedMorale,
    WarriorHasFled,
    WarriorImprovedStats,
    WarriorLostMorale,
    WarriorTookDamage,
    WarriorWasCaptured,
    WarriorWasIncapacitated,
    WarriorWasKilled,
)
from apps.skirmish.tests.factories.skirmish import SkirmishFactory
from apps.skirmish.tests.factories.warrior import WarriorFactory


def test_handle_log_warrior_takes_damage_logs_both_rolls():
    skirmish = SkirmishFactory.build()
    attacker = WarriorFactory.build(name="Beorn")
    defender = WarriorFactory.build(name="Cuthred")

    result = handle_log_warrior_takes_damage(
        context=WarriorTookDamage(
            skirmish=skirmish,
            attacker=attacker,
            attacker_damage=7,
            defender=defender,
            defender_damage=2,
            damage=5,
        )
    )

    assert result == CreateBattleHistory(
        skirmish=skirmish,
        message="Beorn strikes at 7 against Cuthred's 2 defense, and 5 damage gets through.",
    )


def test_handle_log_warrior_takes_damage_when_the_defence_outrolls_the_attack():
    """
    Armour heavier than the weapon facing it still lets a share of the blow through, so the line may
    not read as a subtraction of the one roll from the other.
    """
    skirmish = SkirmishFactory.build()
    attacker = WarriorFactory.build(name="Beorn")
    defender = WarriorFactory.build(name="Cuthred")

    result = handle_log_warrior_takes_damage(
        context=WarriorTookDamage(
            skirmish=skirmish,
            attacker=attacker,
            attacker_damage=12,
            defender=defender,
            defender_damage=20,
            damage=3,
        )
    )

    assert result == CreateBattleHistory(
        skirmish=skirmish,
        message="Beorn strikes at 12 against Cuthred's 20 defense, and 3 damage gets through.",
    )


def test_handle_log_warrior_defends_all_damage_logs_the_successful_defense():
    skirmish = SkirmishFactory.build()
    attacker = WarriorFactory.build(name="Beorn")
    defender = WarriorFactory.build(name="Cuthred")

    result = handle_log_warrior_defends_all_damage(
        context=WarriorDefendedAllDamage(
            skirmish=skirmish,
            attacker=attacker,
            attacker_damage=2,
            defender=defender,
            defender_damage=7,
            defender_action=SkirmishActionChoices.SIMPLE_ATTACK,
        )
    )

    assert result == CreateBattleHistory(
        skirmish=skirmish,
        message="Cuthred defended 2 damage from Beorn with 7 defense.",
    )


def test_handle_log_attacker_defender_decided_logs_the_chosen_action():
    skirmish = SkirmishFactory.build()
    attacker = WarriorFactory.build(name="Beorn")
    defender = WarriorFactory.build(name="Cuthred")

    result = handle_log_attacker_defender_decided(
        context=AttackerDefenderDecided(
            skirmish=skirmish,
            attacker=attacker,
            attacker_action=SkirmishActionChoices.RISKY_ATTACK,
            defender=defender,
            defender_action=SkirmishActionChoices.DEFENSIVE_STANCE,
        )
    )

    assert result == CreateBattleHistory(
        skirmish=skirmish,
        message="Beorn is the attacker and Cuthred the defender and chooses to attack with a Risky attack.",
    )


def test_handle_log_warrior_incapacitation_logs_the_knockout():
    skirmish = SkirmishFactory.build()
    warrior = WarriorFactory.build(name="Cuthred")

    result = handle_log_warrior_incapacitation(
        context=WarriorWasIncapacitated(
            skirmish=skirmish, warrior=warrior, by_warrior=WarriorFactory.build(name="Beorn")
        )
    )

    assert result == CreateBattleHistory(skirmish=skirmish, message="Cuthred is out of the fight being unconscious.")


def test_handle_log_warrior_death_logs_the_kill():
    skirmish = SkirmishFactory.build()
    warrior = WarriorFactory.build(name="Cuthred")

    result = handle_log_warrior_death(
        context=WarriorWasKilled(skirmish=skirmish, warrior=warrior, by_warrior=WarriorFactory.build(name="Beorn"))
    )

    assert result == CreateBattleHistory(skirmish=skirmish, message="Cuthred is out of the fight being killed.")


def test_handle_log_round_finished_names_the_round_that_resolved():
    """
    The number comes off the event, not off the skirmish: by the time this runs "current_round" has
    already been incremented to the round nobody has fought yet.
    """
    skirmish = SkirmishFactory.build(current_round=4)

    result = handle_log_round_finished(context=RoundFinished(skirmish=skirmish, round_number=3, victor=None, month=3))

    assert result == CreateBattleHistory(skirmish=skirmish, message="Round 3 finished.")


def test_handle_log_skirmish_finished_logs_the_victor():
    skirmish = SkirmishFactory.build(victorious_faction=FactionFactory.build(name="Mercia"))

    result = handle_log_skirmish_finished(
        context=SkirmishFinished(
            skirmish=skirmish,
            incapacitated_warriors=[],
            defeated_unconscious_warriors=[],
            victorious_healthy_warriors=[],
            quest_name="Raid cattle",
            quest_loot=250,
            month=3,
        )
    )

    assert result == CreateBattleHistory(skirmish=skirmish, message="Skirmish finished. Mercia won.")


def test_handle_log_item_dropped_logs_the_item_name():
    skirmish = SkirmishFactory.build()
    warrior = WarriorFactory.build(name="Cuthred")

    result = handle_log_item_dropped(
        context=ItemDroppedAsLoot(
            skirmish=skirmish,
            warrior=warrior,
            item=ItemFactory.build(),
            item_name="Superior Battle axe",
            new_owner=FactionFactory.build(),
        )
    )

    assert result == CreateBattleHistory(skirmish=skirmish, message="Cuthred dropped the item 'Superior Battle axe'")


def test_handle_warrior_is_captured_logs_the_arrest():
    skirmish = SkirmishFactory.build()
    warrior = WarriorFactory.build(name="Cuthred")

    result = handle_warrior_is_captured(
        context=WarriorWasCaptured(skirmish=skirmish, warrior=warrior, capturing_faction=FactionFactory.build())
    )

    assert result == CreateBattleHistory(skirmish=skirmish, message="Cuthred was captured and arrested.")


def test_handle_warrior_is_captured_of_an_occupation():
    """
    A leader seized in an occupied town was taken without a fight, so there is no battle log to
    write the line into.
    """
    result = handle_warrior_is_captured(
        context=WarriorWasCaptured(
            skirmish=None, warrior=WarriorFactory.build(), capturing_faction=FactionFactory.build()
        )
    )

    assert result is None


def test_handle_warrior_gains_morale_logs_the_gained_points():
    skirmish = SkirmishFactory.build()
    warrior = WarriorFactory.build(name="Beorn")

    result = handle_warrior_gains_morale(
        context=WarriorGainedMorale(skirmish=skirmish, warrior=warrior, gained_morale=2)
    )

    assert result == CreateBattleHistory(skirmish=skirmish, message="Beorn gained 2 morale.")


def test_handle_warrior_lost_morale_logs_the_lost_points():
    skirmish = SkirmishFactory.build()
    warrior = WarriorFactory.build(name="Cuthred")

    result = handle_warrior_lost_morale(context=WarriorLostMorale(skirmish=skirmish, warrior=warrior, lost_morale=2))

    assert result == CreateBattleHistory(skirmish=skirmish, message="Cuthred lost 2 morale.")


def test_handle_warrior_has_fled_logs_the_retreat():
    skirmish = SkirmishFactory.build()
    warrior = WarriorFactory.build(name="Cuthred")

    result = handle_warrior_has_fled(context=WarriorHasFled(skirmish=skirmish, warrior=warrior))

    assert result == CreateBattleHistory(skirmish=skirmish, message="Cuthred is out of morale and fled the field.")


def test_handle_warrior_gained_experience_logs_the_gained_points():
    skirmish = SkirmishFactory.build()
    warrior = WarriorFactory.build(name="Beorn")

    result = handle_warrior_gained_experience(
        context=WarriorGainedExperience(skirmish=skirmish, warrior=warrior, gained_experience=25)
    )

    assert result == CreateBattleHistory(skirmish=skirmish, message="Beorn gained 25 experience.")


def test_handle_warrior_gained_level_logs_the_new_level():
    skirmish = SkirmishFactory.build()
    warrior = WarriorFactory.build(name="Beorn")

    result = handle_warrior_gained_level(context=WarriorGainedLevel(skirmish=skirmish, warrior=warrior, level=4))

    assert result == CreateBattleHistory(skirmish=skirmish, message="Beorn reached level 4.")


def test_handle_warrior_improved_stats_logs_the_growth_and_the_new_wage():
    skirmish = SkirmishFactory.build()
    warrior = WarriorFactory.build(name="Beorn")

    result = handle_warrior_improved_stats(
        context=WarriorImprovedStats(
            skirmish=skirmish,
            warrior=warrior,
            gained_strength=1,
            gained_dexterity=1,
            gained_max_health=2,
            gained_max_morale=1,
            gained_salary=15,
            new_monthly_salary=165,
        )
    )

    assert result == CreateBattleHistory(
        skirmish=skirmish,
        message="Beorn grew stronger: strength +1, dexterity +1, health +2, morale +1 — "
        "and now costs 165 silver a month.",
    )


def test_handle_warrior_dropped_silver_logs_the_loot():
    skirmish = SkirmishFactory.build()
    warrior = WarriorFactory.build(name="Cuthred")

    result = handle_warrior_dropped_silver(
        context=WarriorDroppedSilver(
            skirmish=skirmish,
            warrior=warrior,
            gaining_faction=FactionFactory.build(),
            amount=50,
            month=3,
        )
    )

    assert result == CreateBattleHistory(skirmish=skirmish, message="Cuthred dropped 50 silver.")
