from apps.item.tests.factories.item import ItemFactory
from apps.skirmish.handlers.events.skirmish_report import (
    handle_record_gained_experience,
    handle_record_gained_level,
    handle_record_improved_stats,
    handle_record_looted_item,
    handle_record_looted_silver,
    handle_record_quest_reward,
)
from apps.skirmish.messages.commands.skirmish_report import RecordSkirmishSpoil, RecordWarriorGrowth
from apps.skirmish.messages.events.item import ItemDroppedAsLoot
from apps.skirmish.messages.events.skirmish import SkirmishFinished
from apps.skirmish.messages.events.transaction import WarriorDroppedSilver
from apps.skirmish.messages.events.warrior import WarriorGainedExperience, WarriorGainedLevel, WarriorImprovedStats
from apps.skirmish.models.skirmish_spoil import SkirmishSpoil
from apps.skirmish.tests.factories.skirmish import SkirmishFactory
from apps.skirmish.tests.factories.warrior import WarriorFactory


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
