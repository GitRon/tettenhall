from apps.core.domain import message_registry
from apps.core.event_loop.messages import Command
from apps.skirmish.choices.skirmish_action import SkirmishActionChoices
from apps.skirmish.messages.commands.skirmish import (
    WarriorAttacksWarriorWithFastAttack,
    WarriorAttacksWarriorWithRiskyAttack,
    WarriorAttacksWarriorWithSimpleAttack,
    WinSkirmish,
)
from apps.skirmish.messages.events import skirmish
from apps.skirmish.models.skirmish import Skirmish
from apps.skirmish.models.warrior import Warrior


@message_registry.register_event(event=skirmish.AttackerDefenderDecided)
def handle_attacker_defender_decided(*, context: skirmish.AttackerDefenderDecided.Context) -> Command:
    if context.attack_action == SkirmishActionChoices.SIMPLE_ATTACK:
        # TODO: move attack type to context
        command = WarriorAttacksWarriorWithSimpleAttack(
            WarriorAttacksWarriorWithSimpleAttack.Context(
                skirmish=context.skirmish,
                attacker=context.attacker,
                defender=context.defender,
            )
        )
    elif context.attack_action == SkirmishActionChoices.RISKY_ATTACK:
        command = WarriorAttacksWarriorWithRiskyAttack(
            WarriorAttacksWarriorWithRiskyAttack.Context(
                skirmish=context.skirmish,
                attacker=context.attacker,
                defender=context.defender,
            )
        )
    elif context.attack_action == SkirmishActionChoices.FAST_ATTACK:
        command = WarriorAttacksWarriorWithFastAttack(
            WarriorAttacksWarriorWithFastAttack.Context(
                skirmish=context.skirmish,
                attacker=context.attacker,
                defender=context.defender,
            )
        )
    else:
        raise RuntimeError("Invalid attack action")
    return command


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
