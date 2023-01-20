from apps.core.domain import message_registry
from apps.skirmish.messages.commands.skirmish import (
    WarriorAttacksWarriorWithRiskyAttack,
    WarriorAttacksWarriorWithSimpleAttack,
    WinSkirmish,
)
from apps.skirmish.messages.events import skirmish
from apps.skirmish.models.skirmish import Skirmish
from apps.skirmish.models.warrior import FightAction, Warrior


@message_registry.register_event(event=skirmish.AttackerDefenderDecided)
def handle_attacker_defender_decided(context: skirmish.AttackerDefenderDecided.Context):
    if context.attack_action == FightAction.TypeChoices.SIMPLE_ATTACK:
        # todo move attack type to context
        command = WarriorAttacksWarriorWithSimpleAttack.generator(
            context_data={
                "skirmish": context.skirmish,
                "attacker": context.attacker,
                "defender": context.defender,
            }
        )
    elif context.attack_action == FightAction.TypeChoices.RISKY_ATTACK:
        command = WarriorAttacksWarriorWithRiskyAttack.generator(
            context_data={
                "skirmish": context.skirmish,
                "attacker": context.attacker,
                "defender": context.defender,
            }
        )
    else:
        raise RuntimeError("Invalid attack action")
    return command


@message_registry.register_event(event=skirmish.RoundFinished)
def handle_round_finished(context: skirmish.RoundFinished.Context):
    Skirmish.objects.increment_round(skirmish=context.skirmish)

    if not context.skirmish.non_player_warriors.filter(condition=Warrior.ConditionChoices.CONDITION_HEALTHY).exists():
        return WinSkirmish.generator(
            context_data={"skirmish": context.skirmish, "victorious_faction": context.skirmish.player_faction}
        )
    elif not context.skirmish.player_warriors.filter(condition=Warrior.ConditionChoices.CONDITION_HEALTHY).exists():
        return WinSkirmish.generator(
            context_data={"skirmish": context.skirmish, "victorious_faction": context.skirmish.non_player_faction}
        )
