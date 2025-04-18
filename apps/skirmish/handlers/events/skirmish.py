from queuebie import message_registry
from queuebie.messages import Command

from apps.skirmish.messages.commands.skirmish import (
    WarriorAttacksWarrior,
    WinSkirmish,
)
from apps.skirmish.messages.events import skirmish


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
