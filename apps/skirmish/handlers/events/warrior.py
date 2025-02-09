from queuebie import message_registry
from queuebie.messages import Command

from apps.skirmish.messages.commands.skirmish import DetermineAttacker
from apps.skirmish.messages.commands.warrior import CaptureWarrior, IncreaseExperience, IncreaseMorale, ReduceMorale
from apps.skirmish.messages.events import skirmish, warrior
from apps.skirmish.messages.events.warrior import WarriorWasIncapacitated, WarriorWasKilled
from apps.skirmish.models.warrior import Warrior


@message_registry.register_event(event=skirmish.FighterPairsMatched)
def handle_determine_attacker(*, context: skirmish.FighterPairsMatched) -> Command:
    return DetermineAttacker(
        skirmish=context.skirmish,
        warrior_1=context.warrior_1,
        warrior_2=context.warrior_2,
        action_1=context.attack_action_1,
        action_2=context.attack_action_2,
    )


@message_registry.register_event(event=warrior.WarriorTookDamage)
def handle_reduce_health_and_update_condition(*, context: warrior.WarriorTookDamage) -> list[Command]:
    message_list = []

    # Reduce health
    context.defender = Warrior.objects.reduce_current_health(
        obj=context.defender,
        damage=context.damage,
    )

    # Taking damages causes loss of 10% morale
    message_list.append(
        ReduceMorale(
            skirmish=context.skirmish,
            warrior=context.defender,
            lost_morale=context.defender.max_morale * 0.1,
        )
    )

    # Update condition
    # TODO: move to "reduce_current_health"
    if context.defender.current_health <= 0:
        if context.defender.current_health < context.defender.max_health * -0.15:
            condition = Warrior.ConditionChoices.CONDITION_DEAD
            message_list.append(
                WarriorWasKilled(
                    skirmish=context.skirmish,
                    warrior=context.defender,
                    by_warrior=context.attacker,
                )
            )
        else:
            condition = Warrior.ConditionChoices.CONDITION_UNCONSCIOUS
            message_list.append(
                WarriorWasIncapacitated(
                    skirmish=context.skirmish,
                    warrior=context.defender,
                    by_warrior=context.attacker,
                )
            )

        Warrior.objects.set_condition(obj=context.defender, condition=condition)

    return message_list


@message_registry.register_event(event=warrior.WarriorHasFled)
@message_registry.register_event(event=warrior.WarriorWasIncapacitated)
@message_registry.register_event(event=warrior.WarriorWasKilled)
def handle_morale_drop_on_faction_on_warrior_is_out_of_fight(
    *,
    context: [
        warrior.WarriorHasFled,
        warrior.WarriorWasIncapacitated,
        warrior.WarriorWasKilled,
    ],
) -> list[Command]:
    message_list = []

    if context.warrior.faction == context.skirmish.player_faction:
        affected_warrior_list = context.skirmish.player_warriors.filter(
            condition=Warrior.ConditionChoices.CONDITION_HEALTHY
        )
    else:
        affected_warrior_list = context.skirmish.non_player_warriors.filter(
            condition=Warrior.ConditionChoices.CONDITION_HEALTHY
        )

    # Every other warrior from the faction participating in this battle will lose 10% morale
    for affected_warrior in affected_warrior_list:
        if affected_warrior != context.warrior:
            message_list.append(
                ReduceMorale(
                    skirmish=context.skirmish,
                    warrior=affected_warrior,
                    lost_morale=context.warrior.max_morale * 0.1,
                )
            )

    return message_list


@message_registry.register_event(event=warrior.WarriorWasIncapacitated)
@message_registry.register_event(event=warrior.WarriorWasKilled)
def handle_experience_gain_on_warrior_incapacitation(
    *,
    context: [warrior.WarriorWasIncapacitated, warrior.WarriorWasKilled],
) -> Command:
    gained_experience = 25

    return IncreaseExperience(
        skirmish=context.skirmish,
        warrior=context.by_warrior,
        increased_experience=gained_experience,
    )


@message_registry.register_event(event=warrior.WarriorDefendedAllDamage)
def handle_morale_increase_on_warriors_defends_all_damage(*, context: warrior.WarriorDefendedAllDamage) -> Command:
    return IncreaseMorale(
        skirmish=context.skirmish,
        warrior=context.defender,
        increased_morale=context.defender.max_morale * 0.1,
    )


@message_registry.register_event(event=skirmish.SkirmishFinished)
def handle_capture_unsconcious_warriors(*, context: skirmish.SkirmishFinished) -> list[Command]:
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
            CaptureWarrior(
                skirmish=context.skirmish,
                warrior=captured_warrior,
                capturing_faction=context.skirmish.victorious_faction,
            )
        )

    return message_list


@message_registry.register_event(event=skirmish.SkirmishFinished)
def handle_experience_gain_after_battle_for_victor(*, context: skirmish.SkirmishFinished) -> list[Command]:
    message_list = []

    gained_experience = 10

    if context.skirmish.victorious_faction == context.skirmish.player_faction:
        affected_warrior_qs = context.skirmish.player_warriors.filter(
            condition=Warrior.ConditionChoices.CONDITION_HEALTHY
        )
    else:
        affected_warrior_qs = context.skirmish.non_player_warriors.filter(
            condition=Warrior.ConditionChoices.CONDITION_HEALTHY
        )

    for affected_warrior in affected_warrior_qs:
        message_list.append(
            IncreaseExperience(
                skirmish=context.skirmish,
                warrior=affected_warrior,
                increased_experience=gained_experience,
            )
        )

    return message_list
