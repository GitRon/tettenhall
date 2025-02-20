from queuebie import message_registry
from queuebie.messages import Command

from apps.skirmish.messages.commands.skirmish import (
    WarriorAttacksWarrior,
    WinSkirmish,
)
from apps.skirmish.messages.events import skirmish
from apps.skirmish.models.skirmish import Skirmish
from apps.skirmish.models.warrior import Warrior


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
    Skirmish.objects.increment_round(skirmish=context.skirmish)

    if not context.skirmish.non_player_warriors.filter(condition=Warrior.ConditionChoices.CONDITION_HEALTHY).exists():
        return WinSkirmish(
            skirmish=context.skirmish, victorious_faction=context.skirmish.player_faction, month=context.month
        )
    if not context.skirmish.player_warriors.filter(condition=Warrior.ConditionChoices.CONDITION_HEALTHY).exists():
        return WinSkirmish(
            skirmish=context.skirmish, victorious_faction=context.skirmish.non_player_faction, month=context.month
        )

    return None
