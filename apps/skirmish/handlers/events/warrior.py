from apps.core.domain import message_registry
from apps.skirmish.messages.commands.skirmish import DetermineAttacker
from apps.skirmish.messages.commands.warrior import CaptureWarrior, IncreaseMorale, ReduceMorale
from apps.skirmish.messages.events import skirmish, warrior
from apps.skirmish.messages.events.warrior import WarriorLostMorale, WarriorWasIncapacitated, WarriorWasKilled
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
    message_list = []

    # Reduce health
    Warrior.objects.reduce_current_health(
        obj=context.defender,
        damage=context.damage,
    )

    # Taking damages causes loss of 10% morale
    message_list.append(
        ReduceMorale.generator(
            context_data={
                "skirmish": context.skirmish,
                "warrior": context.defender,
                "lost_morale": context.defender.max_morale * 0.1,
            }
        )
    )

    # Update condition
    # todo move to "reduce_current_health"
    if context.defender.current_health < 0:
        if context.defender.current_health < context.defender.max_health * -0.15:
            condition = Warrior.ConditionChoices.CONDITION_DEAD
            message_list.append(
                WarriorWasKilled.generator(context_data={"skirmish": context.skirmish, "warrior": context.defender})
            )
        else:
            condition = Warrior.ConditionChoices.CONDITION_UNCONSCIOUS
            message_list.append(
                WarriorWasIncapacitated.generator(
                    context_data={"skirmish": context.skirmish, "warrior": context.defender}
                )
            )

        Warrior.objects.set_condition(obj=context.defender, condition=condition)

    return message_list


@message_registry.register_event(event=warrior.WarriorWasIncapacitated)
def handle_morale_drop_on_faction_on_incapacitated_warrior(context: warrior.WarriorWasIncapacitated.Context):
    message_list = []

    if context.warrior.faction == context.skirmish.player_faction:
        affected_warrior_list = context.skirmish.player_warriors.all()
    else:
        affected_warrior_list = context.skirmish.non_player_warriors.all()

    # Every other warrior from the faction participating in this battle will lose 10% morale
    for affected_warrior in affected_warrior_list:
        if affected_warrior != context.warrior:
            message_list.append(
                WarriorLostMorale.generator(
                    context_data={
                        "skirmish": context.skirmish,
                        "warrior": affected_warrior,
                        "lost_morale": context.warrior.max_morale * 0.1,
                    }
                )
            )

    return message_list


@message_registry.register_event(event=warrior.WarriorDefendedAllDamage)
def handle_morale_increase_on_warriors_defends_all_damage(context: warrior.WarriorDefendedAllDamage.Context):
    return IncreaseMorale.generator(
        context_data={
            "skirmish": context.skirmish,
            "warrior": context.defender,
            "increased_morale": context.defender.max_morale * 0.1,
        }
    )


@message_registry.register_event(event=warrior.WarriorWasKilled)
def handle_morale_drop_on_faction_on_killed_warrior(context: warrior.WarriorWasKilled.Context):
    message_list = []

    if context.warrior.faction == context.skirmish.player_faction:
        affected_warrior_list = context.skirmish.player_warriors.all()
    else:
        affected_warrior_list = context.skirmish.non_player_warriors.all()

    # Every other warrior from the faction participating in this battle will lose 10% morale
    for affected_warrior in affected_warrior_list:
        if affected_warrior != context.warrior:
            message_list.append(
                WarriorLostMorale.generator(
                    context_data={
                        "skirmish": context.skirmish,
                        "warrior": affected_warrior,
                        "lost_morale": context.warrior.max_morale * 0.1,
                    }
                )
            )

    return message_list


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
            CaptureWarrior.generator(
                context_data={
                    "skirmish": context.skirmish,
                    "warrior": captured_warrior,
                    "capturing_faction": context.skirmish.victorious_faction,
                }
            )
        )

    return message_list
