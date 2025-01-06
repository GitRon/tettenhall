from apps.core.domain import message_registry
from apps.core.event_loop.messages import Command
from apps.skirmish.messages.commands.skirmish import (
    WinSkirmish,
)
from apps.skirmish.messages.events import skirmish
from apps.skirmish.models.skirmish import Skirmish
from apps.skirmish.models.warrior import Warrior
from apps.skirmish.services.actions.utils import get_service_by_attack_action


@message_registry.register_event(event=skirmish.AttackerDefenderDecided)
def handle_attacker_defender_decided(*, context: skirmish.AttackerDefenderDecided.Context) -> Command:
    attack_service_class = get_service_by_attack_action(attack_action=context.attack_action)
    return attack_service_class.command(
        attack_service_class.command.Context(
            skirmish=context.skirmish,
            attacker=context.attacker,
            defender=context.defender,
        )
    )


@message_registry.register_event(event=skirmish.RoundFinished)
def handle_round_finished(*, context: skirmish.RoundFinished.Context) -> Command | None:
    Skirmish.objects.increment_round(skirmish=context.skirmish)

    if not context.skirmish.non_player_warriors.filter(condition=Warrior.ConditionChoices.CONDITION_HEALTHY).exists():
        return WinSkirmish(
            WinSkirmish.Context(skirmish=context.skirmish, victorious_faction=context.skirmish.player_faction)
        )
    if not context.skirmish.player_warriors.filter(condition=Warrior.ConditionChoices.CONDITION_HEALTHY).exists():
        return WinSkirmish(
            WinSkirmish.Context(skirmish=context.skirmish, victorious_faction=context.skirmish.non_player_faction)
        )

    return None
