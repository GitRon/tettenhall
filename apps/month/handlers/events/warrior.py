from queuebie import message_registry
from queuebie.messages import Command

from apps.month.messages.commands.month import CreatePlayerMonthLog
from apps.month.models.player_month_log import PlayerMonthLog
from apps.warrior.messages.events.warrior import (
    WarriorDesertedOverUnpaidSalary,
    WarriorHealthHealed,
    WarriorMoraleReplenished,
)


@message_registry.register_event(event=WarriorMoraleReplenished)
def handle_warrior_morale_replenished(*, context: WarriorMoraleReplenished) -> Command:
    # The faction comes off the event, not off the warrior. An event handler runs behind the database
    # blocker, and "warrior.faction" is only free when something upstream happened to leave the
    # relation cached - a "refresh_from_db" in the command handler that raised this drops it, and the
    # read that follows is a query in a place that may not make one. The event carries what is needed.
    return CreatePlayerMonthLog(
        title=f"Morale of warrior {context.warrior} was replenished to the maximum.",
        kind=PlayerMonthLog.KindChoices.KIND_MORALE_RECOVERED,
        month=context.month,
        faction=context.faction,
    )


@message_registry.register_event(event=WarriorHealthHealed)
def handle_warrior_health_healed(*, context: WarriorHealthHealed) -> Command:
    return CreatePlayerMonthLog(
        title=f"Warrior {context.warrior} healed {context.healed_points} HP.",
        kind=PlayerMonthLog.KindChoices.KIND_WOUNDS_HEALED,
        month=context.month,
        faction=context.faction,
    )


@message_registry.register_event(event=WarriorDesertedOverUnpaidSalary)
def handle_warrior_deserted_over_unpaid_salary(*, context: WarriorDesertedOverUnpaidSalary) -> Command:
    # The faction comes off the event rather than off the warrior: desertion clears his own FK, so
    # by the time this runs there is nothing on him left to log against
    return CreatePlayerMonthLog(
        title=f"{context.warrior} left the war band over unpaid wages.",
        kind=PlayerMonthLog.KindChoices.KIND_WARRIOR_DESERTED,
        month=context.month,
        faction=context.faction,
    )
