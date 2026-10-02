from queuebie import message_registry
from queuebie.messages import Command

from apps.warband.skirmish.messages.commands.skirmish import (
    CreateSkirmish,
    SendLocalsHome,
    TakeRaidYield,
    WarriorAttacksWarrior,
    WinSkirmish,
)
from apps.warband.skirmish.messages.events import skirmish
from apps.warband.skirmish.raids import get_raid_kind


@message_registry.register_event(event=skirmish.FactionWasAttacked)
def handle_create_skirmish_for_attack(*, context: skirmish.FactionWasAttacked) -> Command:
    # Nothing but mapping here: both rosters were resolved by the command handler that raised this
    return CreateSkirmish(
        name=get_raid_kind(value=context.raid_kind).get_skirmish_name(target=context.defending_faction),
        faction_1=context.attacking_faction,
        faction_2=context.defending_faction,
        warrior_list_1=context.attacking_warriors,
        warrior_list_2=context.defending_warriors,
        local_warriors=context.local_warriors,
        raid_kind=context.raid_kind,
        month=context.month,
        fortification_strength=context.fortification_strength,
    )


@message_registry.register_event(event=skirmish.AttackerDefenderDecided)
def handle_attacker_defender_decided(*, context: skirmish.AttackerDefenderDecided) -> Command:
    return WarriorAttacksWarrior(
        skirmish=context.skirmish,
        round_number=context.round_number,
        attacker=context.attacker,
        attacker_action=context.attacker_action,
        defender=context.defender,
        defender_action=context.defender_action,
        initiative=context.initiative,
    )


@message_registry.register_event(event=skirmish.RoundFinished)
def handle_round_finished(*, context: skirmish.RoundFinished) -> Command | None:
    if context.victor:
        return WinSkirmish(skirmish=context.skirmish, victorious_faction=context.victor, month=context.month)

    return None


@message_registry.register_event(event=skirmish.SkirmishFinished)
def handle_take_raid_yield_after_victory(*, context: skirmish.SkirmishFinished) -> Command | None:
    """
    A raid the attackers won takes what it set out for. One they lost, or one on the burh, takes nothing
    beyond the loot of the field.

    Compared by id, so nothing here follows a relation the database blocker would refuse.
    """
    if context.skirmish.victorious_faction_id != context.skirmish.attacking_faction_id:
        return None

    raid_kind = get_raid_kind(value=context.skirmish.raid_kind)
    if not (raid_kind.PURSE_SHARE or raid_kind.FYRD_NAMES_BURNED):
        return None

    return TakeRaidYield(skirmish=context.skirmish, month=context.month)


@message_registry.register_event(event=skirmish.SkirmishFinished)
def handle_send_locals_home_after_the_fight(*, context: skirmish.SkirmishFinished) -> Command:
    # Which of the skirmish's men are locals is the command handler's to read; it finds nobody for a
    # fight nobody turned out for
    return SendLocalsHome(
        skirmish=context.skirmish,
        defeated_unconscious_warriors=context.defeated_unconscious_warriors,
        month=context.month,
    )
