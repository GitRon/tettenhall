from queuebie import message_registry
from queuebie.messages import Command

from apps.month.messages.commands.month import CreatePlayerMonthLog
from apps.warrior.messages.events.warrior import WarriorHealthHealed, WarriorMoraleReplenished


@message_registry.register_event(event=WarriorMoraleReplenished)
def handle_warrior_morale_replenished(*, context: WarriorMoraleReplenished) -> Command:
    return CreatePlayerMonthLog(
        title=f"Morale of warrior {context.warrior} was replenished to the maximum.",
        month=context.month,
        faction=context.warrior.faction,
    )


@message_registry.register_event(event=WarriorHealthHealed)
def handle_warrior_health_healed(*, context: WarriorHealthHealed) -> Command:
    return CreatePlayerMonthLog(
        title=f"Warrior {context.warrior} healed {context.healed_points} HP.",
        month=context.month,
        faction=context.faction,
    )
