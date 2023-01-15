from apps.core.domain import message_registry
from apps.skirmish.messages.commands.skirmish import DetermineAttacker
from apps.skirmish.messages.commands.warrior import WarriorIsCaptured
from apps.skirmish.messages.events import skirmish, warrior
from apps.skirmish.messages.events.warrior import WarriorWasIncapacitated, WarriorWasKilled
from apps.skirmish.models.warrior import Warrior


@message_registry.register_event(event=skirmish.FighterPairsMatched)
def handle_determine_attacker(context: skirmish.FighterPairsMatched.Context):
    return DetermineAttacker.generator(
        context_data={
            "skirmish": context.skirmish,
            "warrior_1": context.warrior_1,
            "warrior_2": context.warrior_2,
            "action_1": context.attack_action_1,
            "action_2": context.attack_action_2,
        }
    )


@message_registry.register_event(event=warrior.WarriorTookDamage)
def handle_reduce_health_and_update_condition(context: warrior.WarriorTookDamage.Context):
    # Reduce health
    Warrior.objects.reduce_current_health(
        obj=context.defender,
        damage=context.damage,
    )

    # Update condition
    message = None
    condition = Warrior.ConditionChoices.CONDITION_HEALTHY
    if context.defender.current_health < 0:
        if context.defender.current_health < context.defender.max_health * -0.15:
            condition = Warrior.ConditionChoices.CONDITION_DEAD
            message = WarriorWasKilled.generator(
                context_data={"skirmish": context.skirmish, "warrior": context.defender}
            )
        else:
            condition = Warrior.ConditionChoices.CONDITION_UNCONSCIOUS
            message = WarriorWasIncapacitated.generator(
                context_data={"skirmish": context.skirmish, "warrior": context.defender}
            )

    Warrior.objects.set_condition(obj=context.defender, condition=condition)

    if message:
        return message


@message_registry.register_event(event=skirmish.SkirmishFinished)
def handle_capture_unsconcious_warriors(context: skirmish.SkirmishFinished.Context):
    message_list = []

    if context.skirmish.victorious_faction == context.skirmish.player_faction:
        unsconcious_warrior_list = context.skirmish.non_player_warriors.filter(
            condition=Warrior.ConditionChoices.CONDITION_UNCONSCIOUS
        )
    else:
        unsconcious_warrior_list = context.skirmish.player_warriors.filter(
            condition=Warrior.ConditionChoices.CONDITION_UNCONSCIOUS
        )

    for captured_warrior in unsconcious_warrior_list:
        message_list.append(
            WarriorIsCaptured.generator(
                context_data={
                    "skirmish": context.skirmish,
                    "warrior": captured_warrior,
                    "capturing_faction": context.skirmish.victorious_faction,
                }
            )
        )

    return message_list
