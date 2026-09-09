"""
The structured half of what the battle log says in prose.

Every handler here has a twin in ``handlers/events/battle_history.py`` reading the same event. The
log narrates the fight while it happens; these rows are what a report of the finished fight is
assembled from, and a summary that had to parse its own English instead would break on every
rewording.
"""

from queuebie import message_registry
from queuebie.messages import Command

from apps.warband.skirmish.choices.blow_outcome import BlowOutcomeChoices
from apps.warband.skirmish.messages.commands.skirmish_report import (
    RecordSkirmishBlow,
    RecordSkirmishCasualty,
    RecordSkirmishSpoil,
    RecordWarriorGrowth,
)
from apps.warband.skirmish.messages.events import item, skirmish, transaction, warrior
from apps.warband.skirmish.models import SkirmishCasualty, SkirmishSpoil


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


@message_registry.register_event(event=warrior.WarriorWasKilled)
def handle_record_killed_warrior(*, context: warrior.WarriorWasKilled) -> Command:
    return RecordSkirmishCasualty(
        skirmish=context.skirmish,
        warrior=context.warrior,
        fate=SkirmishCasualty.FateChoices.FATE_KILLED,
    )


@message_registry.register_event(event=warrior.WarriorWasIncapacitated)
def handle_record_incapacitated_warrior(*, context: warrior.WarriorWasIncapacitated) -> Command:
    """
    A man left lying on the field, which is not yet the same thing as a man lost.

    The beaten side's unconscious are taken prisoner once the fight is decided and this row is
    overwritten; the winner's keep their gear and their place on the roster, and this is the whole
    of what happened to them.
    """
    return RecordSkirmishCasualty(
        skirmish=context.skirmish,
        warrior=context.warrior,
        fate=SkirmishCasualty.FateChoices.FATE_INCAPACITATED,
    )


@message_registry.register_event(event=warrior.WarriorWasCaptured)
def handle_record_captured_warrior(*, context: warrior.WarriorWasCaptured) -> Command | None:
    # A leader seized in an occupied town was taken without a fight, so there is no fight for the
    # capture to be a casualty of - the same refusal the battle log makes
    if context.skirmish is None:
        return None

    return RecordSkirmishCasualty(
        skirmish=context.skirmish,
        warrior=context.warrior,
        fate=SkirmishCasualty.FateChoices.FATE_CAPTURED,
    )


@message_registry.register_event(event=warrior.WarriorHasFled)
def handle_record_routed_warrior(*, context: warrior.WarriorHasFled) -> Command:
    """
    Recorded although it costs the player nothing: he keeps his gear and rallies next month.

    It is here because a report that only named the fallen could not account for the men - five
    marched and three fought, and nothing else on the panel says where the other two went.
    """
    return RecordSkirmishCasualty(
        skirmish=context.skirmish,
        warrior=context.warrior,
        fate=SkirmishCasualty.FateChoices.FATE_FLED,
    )


@message_registry.register_event(event=warrior.WarriorTookDamage)
def handle_record_landed_blow(*, context: warrior.WarriorTookDamage) -> Command:
    """
    A blow that got through. The outcome is stated rather than carried, because this event is raised
    for nothing else - damage above zero is what makes it this event and not the other one.
    """
    return RecordSkirmishBlow(
        skirmish=context.skirmish,
        round_number=context.round_number,
        attacker=context.attacker,
        attacker_action=context.attacker_action,
        attack=context.attack,
        defender=context.defender,
        defender_action=context.defender_action,
        defense=context.defense,
        outcome=BlowOutcomeChoices.OUTCOME_HIT,
        damage=context.damage,
    )


@message_registry.register_event(event=warrior.WarriorDefendedAllDamage)
def handle_record_stopped_blow(*, context: warrior.WarriorDefendedAllDamage) -> Command:
    """
    An exchange that cost the defender nothing, which is three different things and says which.
    """
    return RecordSkirmishBlow(
        skirmish=context.skirmish,
        round_number=context.round_number,
        attacker=context.attacker,
        attacker_action=context.attacker_action,
        attack=context.attack,
        defender=context.defender,
        defender_action=context.defender_action,
        defense=context.defense,
        outcome=context.outcome,
    )
