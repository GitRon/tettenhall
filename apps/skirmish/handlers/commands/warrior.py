from queuebie import message_registry
from queuebie.messages import Event

from apps.faction.models.faction import Faction
from apps.skirmish.messages.commands import warrior
from apps.skirmish.messages.commands.warrior import ReduceHealth
from apps.skirmish.messages.events.warrior import (
    LastUsedSkirmishActionStored,
    WarriorGainedExperience,
    WarriorGainedMorale,
    WarriorHasFled,
    WarriorLostMorale,
    WarriorWasCaptured,
    WarriorWasIncapacitated,
    WarriorWasKilled,
)
from apps.skirmish.models.warrior import Warrior


@message_registry.register_command(command=warrior.StoreLastUsedSkirmishAction)
def handle_store_last_used_skirmish_action(*, context: warrior.StoreLastUsedSkirmishAction) -> list[Event] | Event:
    context.warrior.last_used_skirmish_action = context.skirmish_action
    context.warrior.save()

    return LastUsedSkirmishActionStored(
        skirmish=context.skirmish,
        warrior=context.warrior,
        skirmish_action=context.skirmish_action,
    )


@message_registry.register_command(command=warrior.CaptureWarrior)
def handle_warrior_is_captured(*, context: warrior.CaptureWarrior) -> list[Event] | Event:
    Faction.objects.add_captive(faction=context.capturing_faction, warrior=context.warrior)
    context.warrior.faction = None
    context.warrior.save()

    return WarriorWasCaptured(
        skirmish=context.skirmish,
        warrior=context.warrior,
        capturing_faction=context.capturing_faction,
    )


@message_registry.register_command(command=ReduceHealth)
def handle_reduce_warrior_health(*, context: ReduceHealth) -> list[Event]:
    message_list = []

    context.warrior = Warrior.objects.reduce_current_health(obj=context.warrior, damage=context.lost_health)

    # Update condition
    if context.warrior.current_health <= 0:
        if context.warrior.current_health < context.warrior.max_health * -0.15:
            condition = Warrior.ConditionChoices.CONDITION_DEAD
            message_list.append(
                WarriorWasKilled(
                    skirmish=context.skirmish,
                    warrior=context.warrior,
                    by_warrior=context.attacker,
                )
            )
        else:
            condition = Warrior.ConditionChoices.CONDITION_UNCONSCIOUS
            message_list.append(
                WarriorWasIncapacitated(
                    skirmish=context.skirmish,
                    warrior=context.warrior,
                    by_warrior=context.attacker,
                )
            )

        Warrior.objects.set_condition(obj=context.warrior, condition=condition)

    return message_list


@message_registry.register_command(command=warrior.ReduceMorale)
def handle_warrior_losing_morale(*, context: warrior.ReduceMorale) -> list[Event] | Event:
    message_list = []

    # Only health warriors lose morale
    if context.warrior.condition != Warrior.ConditionChoices.CONDITION_HEALTHY:
        return message_list

    context.warrior = Warrior.objects.reduce_morale(obj=context.warrior, lost_morale=context.lost_morale)

    if context.warrior.current_morale <= 0:
        context.warrior = Warrior.objects.set_condition(
            obj=context.warrior, condition=Warrior.ConditionChoices.CONDITION_FLEEING
        )

        message_list.append(
            WarriorHasFled(
                skirmish=context.skirmish,
                warrior=context.warrior,
            )
        )

    if context.lost_morale > 0:
        message_list.append(
            WarriorLostMorale(
                skirmish=context.skirmish,
                warrior=context.warrior,
                lost_morale=context.lost_morale,
            )
        )

    return message_list


@message_registry.register_command(command=warrior.IncreaseMorale)
def handle_warrior_increasing_morale(*, context: warrior.IncreaseMorale) -> list[Event] | Event:
    context.warrior = Warrior.objects.increase_morale(obj=context.warrior, increased_morale=context.increased_morale)

    return WarriorGainedMorale(
        skirmish=context.skirmish,
        warrior=context.warrior,
        gained_morale=context.increased_morale,
    )


@message_registry.register_command(command=warrior.IncreaseExperience)
def handle_warrior_increasing_experience(*, context: warrior.IncreaseExperience) -> list[Event] | Event:
    context.warrior = Warrior.objects.increase_experience(obj=context.warrior, experience=context.increased_experience)

    return WarriorGainedExperience(
        skirmish=context.skirmish,
        warrior=context.warrior,
        gained_experience=context.increased_experience,
    )
