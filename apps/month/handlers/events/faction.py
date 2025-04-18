from queuebie import message_registry
from queuebie.messages import Command

from apps.faction.messages.events.faction import FactionFyrdReserveReplenished, MonthlyWarriorSalariesPaid
from apps.month.messages.commands.month import CreatePlayerMonthLog


@message_registry.register_event(event=FactionFyrdReserveReplenished)
def handle_faction_fyrd_reserve_replenished(*, context: FactionFyrdReserveReplenished) -> Command:
    return CreatePlayerMonthLog(
        title=f"The fyrd has increased and has {context.new_recruitees} new recruitees!",
        month=context.month,
        faction=context.faction,
    )


@message_registry.register_event(event=MonthlyWarriorSalariesPaid)
def handle_pay_monthly_salary(*, context: MonthlyWarriorSalariesPaid) -> Command:
    return CreatePlayerMonthLog(
        title=f"Monthly salaries paid of {context.amount} silver.",
        month=context.month,
        faction=context.faction,
    )
