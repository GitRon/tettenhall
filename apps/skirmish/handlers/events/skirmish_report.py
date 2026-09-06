"""
The structured half of what the battle log says in prose.

Every handler here has a twin in ``handlers/events/battle_history.py`` reading the same event. The
log narrates the fight while it happens; these rows are what a report of the finished fight is
assembled from, and a summary that had to parse its own English instead would break on every
rewording.
"""

from queuebie import message_registry
from queuebie.messages import Command

from apps.skirmish.messages.commands.skirmish_report import RecordSkirmishSpoil, RecordWarriorGrowth
from apps.skirmish.messages.events import item, skirmish, transaction, warrior
from apps.skirmish.models import SkirmishSpoil


@message_registry.register_event(event=item.ItemDroppedAsLoot)
def handle_record_looted_item(*, context: item.ItemDroppedAsLoot) -> Command:
    return RecordSkirmishSpoil(
        skirmish=context.skirmish,
        faction=context.new_owner,
        kind=SkirmishSpoil.KindChoices.KIND_ITEM_TAKEN,
        item=context.item,
        warrior=context.warrior,
    )


@message_registry.register_event(event=transaction.WarriorDroppedSilver)
def handle_record_looted_silver(*, context: transaction.WarriorDroppedSilver) -> Command:
    return RecordSkirmishSpoil(
        skirmish=context.skirmish,
        faction=context.gaining_faction,
        kind=SkirmishSpoil.KindChoices.KIND_SILVER_LOOTED,
        warrior=context.warrior,
        amount=context.amount,
    )


@message_registry.register_event(event=skirmish.SkirmishFinished)
def handle_record_quest_reward(*, context: skirmish.SkirmishFinished) -> Command | None:
    """
    The largest single reward a fight pays, and the one thing about it no relation carries.

    Guarded on the same figure as the payout itself: a contract signed by the side that lost pays
    nothing, and a fight with no contract behind it has nothing to report.
    """
    if context.quest_loot <= 0:
        return None

    return RecordSkirmishSpoil(
        skirmish=context.skirmish,
        faction=context.skirmish.victorious_faction,
        kind=SkirmishSpoil.KindChoices.KIND_QUEST_REWARD,
        amount=context.quest_loot,
        description=context.quest_name,
    )


@message_registry.register_event(event=warrior.WarriorGainedExperience)
def handle_record_gained_experience(*, context: warrior.WarriorGainedExperience) -> Command:
    return RecordWarriorGrowth(
        skirmish=context.skirmish,
        warrior=context.warrior,
        gained_experience=context.gained_experience,
    )


@message_registry.register_event(event=warrior.WarriorGainedLevel)
def handle_record_gained_level(*, context: warrior.WarriorGainedLevel) -> Command:
    return RecordWarriorGrowth(
        skirmish=context.skirmish,
        warrior=context.warrior,
        reached_level=context.level,
    )


@message_registry.register_event(event=warrior.WarriorImprovedStats)
def handle_record_improved_stats(*, context: warrior.WarriorImprovedStats) -> Command:
    return RecordWarriorGrowth(
        skirmish=context.skirmish,
        warrior=context.warrior,
        gained_strength=context.gained_strength,
        gained_dexterity=context.gained_dexterity,
        gained_max_health=context.gained_max_health,
        gained_max_morale=context.gained_max_morale,
        new_monthly_salary=context.new_monthly_salary,
    )
