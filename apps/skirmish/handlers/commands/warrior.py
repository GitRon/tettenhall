from apps.core.domain import message_registry
from apps.core.event_loop.messages import Event
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
def handle_warrior_is_captured(*, context: warrior.CaptureWarrior.Context) -> list[Event] | Event:
    Faction.objects.add_captive(faction=context.capturing_faction, warrior=context.warrior)

    return WarriorWasCaptured(
        WarriorWasCaptured.Context(
            skirmish=context.skirmish,
            warrior=context.warrior,
            capturing_faction=context.capturing_faction,
        )
    )


@message_registry.register_command(command=warrior.ReduceMorale)
def handle_warrior_losing_morale(*, context: warrior.ReduceMorale.Context) -> list[Event] | Event:
    message_list = []

    context.warrior = Warrior.objects.reduce_morale(obj=context.warrior, lost_morale=context.lost_morale)

    if context.warrior.current_morale <= 0:
        context.warrior = Warrior.objects.set_condition(
            obj=context.warrior, condition=Warrior.ConditionChoices.CONDITION_FLEEING
        )

        message_list.append(
            WarriorHasFled(
                WarriorHasFled.Context(
                    skirmish=context.skirmish,
                    warrior=context.warrior,
                )
            )
        )

    message_list.append(
        WarriorLostMorale(
            WarriorLostMorale.Context(
                skirmish=context.skirmish,
                warrior=context.warrior,
                lost_morale=context.lost_morale,
            )
        )
    )

    return message_list


@message_registry.register_command(command=warrior.IncreaseMorale)
def handle_warrior_increasing_morale(*, context: warrior.IncreaseMorale.Context) -> list[Event] | Event:
    context.warrior = Warrior.objects.increase_morale(obj=context.warrior, increased_morale=context.increased_morale)

    return WarriorGainedMorale(
        WarriorGainedMorale.Context(
            skirmish=context.skirmish,
            warrior=context.warrior,
            gained_morale=context.increased_morale,
        )
    )


@message_registry.register_command(command=warrior.IncreaseExperience)
def handle_warrior_increasing_experience(*, context: warrior.IncreaseExperience.Context) -> list[Event] | Event:
    context.warrior = Warrior.objects.increase_experience(obj=context.warrior, experience=context.increased_experience)

    return WarriorGainedExperience(
        WarriorGainedExperience.Context(
            skirmish=context.skirmish,
            warrior=context.warrior,
            gained_experience=context.increased_experience,
        )
    )
