from queuebie import message_registry
from queuebie.messages import Command

from apps.faction.messages.events.faction import (
    FactionFyrdReserveReplenished,
    MonthlyBuildingMoneyEarned,
    MonthlyWarriorSalariesPaid,
)
from apps.month.messages.commands.month import CreatePlayerMonthLog


@message_registry.register_event(event=FactionFyrdReserveReplenished)
def handle_faction_fyrd_reserve_replenished(*, context: FactionFyrdReserveReplenished) -> Command:
    return CreatePlayerMonthLog(
        # The handler only fires for one recruitee upwards, but "1 new recruitees" still read wrong
        title=f"The fyrd has grown by {context.new_recruitees} "
        f"new recruitee{'' if context.new_recruitees == 1 else 's'}!",
        month=context.month,
        faction=context.faction,
    )


@message_registry.register_event(event=MonthlyWarriorSalariesPaid)
def handle_pay_monthly_salary(*, context: MonthlyWarriorSalariesPaid) -> Command:
    return CreatePlayerMonthLog(
        title=f"Monthly salaries of {context.amount} silver paid.",
        month=context.month,
        faction=context.faction,
    )


@message_registry.register_event(event=MonthlyBuildingMoneyEarned)
def handle_monthly_building_earnings(*, context: MonthlyBuildingMoneyEarned) -> Command:
    return CreatePlayerMonthLog(
        title=f"Buildings earned {context.amount} silver this month.",
        month=context.month,
        faction=context.faction,
    )
