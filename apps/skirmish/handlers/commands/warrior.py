from queuebie import message_registry
from queuebie.messages import Event

from apps.faction.models.faction import Faction
from apps.skirmish.messages.commands import warrior
from apps.skirmish.messages.events.warrior import (
    WarriorGainedExperience,
    WarriorGainedMorale,
    WarriorHasFled,
    WarriorLostMorale,
    WarriorWasCaptured,
)
from apps.skirmish.models.warrior import Warrior


@message_registry.register_command(command=warrior.CaptureWarrior)
def handle_warrior_is_captured(*, context: warrior.CaptureWarrior) -> list[Event] | Event:
    Faction.objects.add_captive(faction=context.capturing_faction, warrior=context.warrior)

    return WarriorWasCaptured(
        skirmish=context.skirmish,
        warrior=context.warrior,
        capturing_faction=context.capturing_faction,
    )


@message_registry.register_command(command=warrior.ReduceMorale)
def handle_warrior_losing_morale(*, context: warrior.ReduceMorale) -> list[Event] | Event:
    message_list = []

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
