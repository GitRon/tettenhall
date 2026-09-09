from apps.common.domain.dice import DiceNotation, DiceRoll
from apps.warband.item.tests.factories.item import ItemFactory
from apps.warband.skirmish.choices.blow_outcome import BlowOutcomeChoices
from apps.warband.skirmish.choices.skirmish_action import SkirmishActionChoices
from apps.warband.skirmish.domain.action_roll import ActionRoll
from apps.warband.skirmish.handlers.events.skirmish_report import (
    handle_record_captured_warrior,
    handle_record_gained_experience,
    handle_record_gained_level,
    handle_record_improved_stats,
    handle_record_incapacitated_warrior,
    handle_record_killed_warrior,
    handle_record_landed_blow,
    handle_record_looted_item,
    handle_record_looted_silver,
    handle_record_quest_reward,
    handle_record_routed_warrior,
    handle_record_stopped_blow,
)
from apps.warband.skirmish.messages.commands.skirmish_report import (
    RecordSkirmishBlow,
    RecordSkirmishCasualty,
    RecordSkirmishSpoil,
    RecordWarriorGrowth,
)
from apps.warband.skirmish.messages.events.item import ItemDroppedAsLoot
from apps.warband.skirmish.messages.events.skirmish import SkirmishFinished
from apps.warband.skirmish.messages.events.transaction import WarriorDroppedSilver
from apps.warband.skirmish.messages.events.warrior import (
    WarriorDefendedAllDamage,
    WarriorGainedExperience,
    WarriorGainedLevel,
    WarriorHasFled,
    WarriorImprovedStats,
    WarriorTookDamage,
    WarriorWasCaptured,
    WarriorWasIncapacitated,
    WarriorWasKilled,
)
from apps.warband.skirmish.models.skirmish_casualty import SkirmishCasualty
from apps.warband.skirmish.models.skirmish_spoil import SkirmishSpoil
from apps.warband.skirmish.tests.factories.skirmish import SkirmishFactory
from apps.warband.skirmish.tests.factories.warrior import WarriorFactory


def test_handle_record_looted_item_credits_the_new_owner():
    skirmish = SkirmishFactory.build()
    warrior = WarriorFactory.build()
    item = ItemFactory.build()

    result = handle_record_looted_item(
        context=ItemDroppedAsLoot(
            skirmish=skirmish,
            warrior=warrior,
            item=item,
            item_name="Superior Long sword",
            new_owner=skirmish.attacking_faction,
        )
    )

    assert result == RecordSkirmishSpoil(
        skirmish=skirmish,
        faction=skirmish.attacking_faction,
        kind=SkirmishSpoil.KindChoices.KIND_ITEM_TAKEN,
        item=item,
        warrior=warrior,
    )


def test_handle_record_looted_silver_carries_the_amount():
    skirmish = SkirmishFactory.build()
    warrior = WarriorFactory.build()

    result = handle_record_looted_silver(
        context=WarriorDroppedSilver(
            skirmish=skirmish,
            warrior=warrior,
            gaining_faction=skirmish.attacking_faction,
            amount=12,
            month=3,
        )
    )

    assert result == RecordSkirmishSpoil(
        skirmish=skirmish,
        faction=skirmish.attacking_faction,
        kind=SkirmishSpoil.KindChoices.KIND_SILVER_LOOTED,
        warrior=warrior,
        amount=12,
    )


def test_handle_record_quest_reward_names_the_quest():
    skirmish = SkirmishFactory.build()
    skirmish.victorious_faction = skirmish.attacking_faction

    result = handle_record_quest_reward(
        context=SkirmishFinished(
            skirmish=skirmish,
            incapacitated_warriors=[],
            defeated_unconscious_warriors=[],
            victorious_healthy_warriors=[],
            quest_name="Silence the raiders",
            quest_loot=400,
            month=3,
        )
    )

    assert result == RecordSkirmishSpoil(
        skirmish=skirmish,
        faction=skirmish.attacking_faction,
        kind=SkirmishSpoil.KindChoices.KIND_QUEST_REWARD,
        amount=400,
        description="Silence the raiders",
    )


def test_handle_record_quest_reward_stays_silent_when_nothing_was_paid():
    skirmish = SkirmishFactory.build()

    result = handle_record_quest_reward(
        context=SkirmishFinished(
            skirmish=skirmish,
            incapacitated_warriors=[],
            defeated_unconscious_warriors=[],
            victorious_healthy_warriors=[],
            quest_name=None,
            quest_loot=0,
            month=3,
        )
    )

    assert result is None


def test_handle_record_gained_experience_maps_to_a_growth_command():
    skirmish = SkirmishFactory.build()
    warrior = WarriorFactory.build()

    result = handle_record_gained_experience(
        context=WarriorGainedExperience(skirmish=skirmish, warrior=warrior, gained_experience=25)
    )

    assert result == RecordWarriorGrowth(skirmish=skirmish, warrior=warrior, gained_experience=25)


def test_handle_record_gained_level_maps_to_a_growth_command():
    skirmish = SkirmishFactory.build()
    warrior = WarriorFactory.build()

    result = handle_record_gained_level(context=WarriorGainedLevel(skirmish=skirmish, warrior=warrior, level=3))

    assert result == RecordWarriorGrowth(skirmish=skirmish, warrior=warrior, reached_level=3)


def test_handle_record_improved_stats_carries_the_four_gains_and_the_wage():
    skirmish = SkirmishFactory.build()
    warrior = WarriorFactory.build()

    result = handle_record_improved_stats(
        context=WarriorImprovedStats(
            skirmish=skirmish,
            warrior=warrior,
            gained_strength=1,
            gained_dexterity=2,
            gained_max_health=3,
            gained_max_morale=4,
            gained_salary=5,
            new_monthly_salary=15,
        )
    )

    assert result == RecordWarriorGrowth(
        skirmish=skirmish,
        warrior=warrior,
        gained_strength=1,
        gained_dexterity=2,
        gained_max_health=3,
        gained_max_morale=4,
        new_monthly_salary=15,
    )


def test_handle_record_landed_blow_states_the_outcome_it_is_raised_for():
    skirmish = SkirmishFactory.build()
    attacker = WarriorFactory.build()
    defender = WarriorFactory.build()
    attack = ActionRoll(roll=DiceRoll(notation=DiceNotation(dice_string="2d6", modifier=1), result=9), value=9)
    defense = ActionRoll(roll=DiceRoll(notation=DiceNotation(dice_string="1d4"), result=2), value=2)

    result = handle_record_landed_blow(
        context=WarriorTookDamage(
            skirmish=skirmish,
            round_number=2,
            attacker=attacker,
            attacker_action=SkirmishActionChoices.SIMPLE_ATTACK,
            attack=attack,
            defender=defender,
            defender_action=SkirmishActionChoices.SIMPLE_ATTACK,
            defense=defense,
            damage=7,
        )
    )

    assert result == RecordSkirmishBlow(
        skirmish=skirmish,
        round_number=2,
        attacker=attacker,
        attacker_action=SkirmishActionChoices.SIMPLE_ATTACK,
        attack=attack,
        defender=defender,
        defender_action=SkirmishActionChoices.SIMPLE_ATTACK,
        defense=defense,
        outcome=BlowOutcomeChoices.OUTCOME_HIT,
        damage=7,
    )


def test_handle_record_stopped_blow_carries_which_kind_of_nothing_it_was():
    """
    The outcome comes off the event rather than being decided here: a swing that went wide, a stance
    that threw nothing and armour that held are one zero and three different records.
    """
    skirmish = SkirmishFactory.build()
    attacker = WarriorFactory.build()
    defender = WarriorFactory.build()
    attack = ActionRoll(roll=None, value=0, outcome=BlowOutcomeChoices.OUTCOME_MISSED)
    defense = ActionRoll(roll=DiceRoll(notation=DiceNotation(dice_string="1d4"), result=3), value=3)

    result = handle_record_stopped_blow(
        context=WarriorDefendedAllDamage(
            skirmish=skirmish,
            round_number=2,
            attacker=attacker,
            attacker_action=SkirmishActionChoices.RISKY_ATTACK,
            attack=attack,
            defender=defender,
            defender_action=SkirmishActionChoices.SIMPLE_ATTACK,
            defense=defense,
            outcome=BlowOutcomeChoices.OUTCOME_MISSED,
        )
    )

    assert result == RecordSkirmishBlow(
        skirmish=skirmish,
        round_number=2,
        attacker=attacker,
        attacker_action=SkirmishActionChoices.RISKY_ATTACK,
        attack=attack,
        defender=defender,
        defender_action=SkirmishActionChoices.SIMPLE_ATTACK,
        defense=defense,
        outcome=BlowOutcomeChoices.OUTCOME_MISSED,
    )


def test_handle_record_killed_warrior_records_the_death():
    skirmish = SkirmishFactory.build()
    warrior = WarriorFactory.build()

    result = handle_record_killed_warrior(
        context=WarriorWasKilled(skirmish=skirmish, warrior=warrior, by_warrior=WarriorFactory.build())
    )

    assert result == RecordSkirmishCasualty(
        skirmish=skirmish,
        warrior=warrior,
        fate=SkirmishCasualty.FateChoices.FATE_KILLED,
    )


def test_handle_record_incapacitated_warrior_records_him_as_merely_down():
    skirmish = SkirmishFactory.build()
    warrior = WarriorFactory.build()

    result = handle_record_incapacitated_warrior(
        context=WarriorWasIncapacitated(skirmish=skirmish, warrior=warrior, by_warrior=WarriorFactory.build())
    )

    assert result == RecordSkirmishCasualty(
        skirmish=skirmish,
        warrior=warrior,
        fate=SkirmishCasualty.FateChoices.FATE_INCAPACITATED,
    )


def test_handle_record_captured_warrior_records_the_capture():
    skirmish = SkirmishFactory.build()
    warrior = WarriorFactory.build()

    result = handle_record_captured_warrior(
        context=WarriorWasCaptured(skirmish=skirmish, warrior=warrior, capturing_faction=skirmish.attacking_faction)
    )

    assert result == RecordSkirmishCasualty(
        skirmish=skirmish,
        warrior=warrior,
        fate=SkirmishCasualty.FateChoices.FATE_CAPTURED,
    )


def test_handle_record_captured_warrior_records_nothing_for_a_capture_without_a_fight():
    """
    An occupation takes a leader without a fight, so there is no report for him to be a casualty of.
    """
    skirmish = SkirmishFactory.build()

    result = handle_record_captured_warrior(
        context=WarriorWasCaptured(
            skirmish=None, warrior=WarriorFactory.build(), capturing_faction=skirmish.attacking_faction
        )
    )

    assert result is None


def test_handle_record_routed_warrior_records_the_rout():
    skirmish = SkirmishFactory.build()
    warrior = WarriorFactory.build()

    result = handle_record_routed_warrior(context=WarriorHasFled(skirmish=skirmish, warrior=warrior))

    assert result == RecordSkirmishCasualty(
        skirmish=skirmish,
        warrior=warrior,
        fate=SkirmishCasualty.FateChoices.FATE_FLED,
    )
