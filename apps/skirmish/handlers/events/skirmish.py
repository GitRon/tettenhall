from queuebie import message_registry
from queuebie.messages import Command

from apps.skirmish.messages.commands.skirmish import (
    CreateSkirmish,
    WarriorAttacksWarrior,
    WinSkirmish,
)
from apps.skirmish.messages.events import skirmish


@message_registry.register_event(event=skirmish.FactionWasAttacked)
def handle_create_skirmish_for_attack(*, context: skirmish.FactionWasAttacked) -> Command:
    # Nothing but mapping here: both rosters were resolved by the command handler that raised this
    return CreateSkirmish(
        name=f"Attack on {context.defending_faction}",
        faction_1=context.attacking_faction,
        faction_2=context.defending_faction,
        warrior_list_1=context.attacking_warriors,
        warrior_list_2=context.defending_warriors,
        month=context.month,
        # An attack is nobody's errand, so there is no contract to pay out or to link
        quest_contract=None,
    )


@message_registry.register_event(event=skirmish.AttackerDefenderDecided)
def handle_attacker_defender_decided(*, context: skirmish.AttackerDefenderDecided) -> Command:
    return WarriorAttacksWarrior(
        skirmish=context.skirmish,
        attacker=context.attacker,
        attacker_action=context.attacker_action,
        defender=context.defender,
        defender_action=context.defender_action,
    )


@message_registry.register_event(event=skirmish.RoundFinished)
def handle_round_finished(*, context: skirmish.RoundFinished) -> Command | None:
    if context.victor:
        return WinSkirmish(skirmish=context.skirmish, victorious_faction=context.victor, month=context.month)

    return None
