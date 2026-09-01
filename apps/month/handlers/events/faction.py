from queuebie import message_registry
from queuebie.messages import Command

from apps.faction.messages.events.faction import (
    FactionFyrdReserveReplenished,
    MonthlyBuildingMoneyEarned,
    MonthlyWarriorSalariesPaid,
    MonthlyWarriorSalariesUnpaid,
)
from apps.month.messages.commands.month import CreatePlayerMonthLog


@message_registry.register_event(event=FactionFyrdReserveReplenished)
def handle_faction_fyrd_reserve_replenished(*, context: FactionFyrdReserveReplenished) -> Command:
    return CreatePlayerMonthLog(
        # The handler only fires for one man upwards, but "1 new recruits" still read wrong
        title=f"The fyrd has grown by {context.new_recruits} new recruit{'' if context.new_recruits == 1 else 's'}!",
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


@message_registry.register_event(event=MonthlyWarriorSalariesUnpaid)
def handle_unpaid_warrior_salaries(*, context: MonthlyWarriorSalariesUnpaid) -> Command:
    # The one cost in the game the player never chose to take on, so it gets said plainly. One line
    # for the whole shortfall rather than one per man: the men who walk get their own lines, and the
    # ones who only lost heart are visible on the roster
    unpaid_warriors = len(context.warrior_list)

    return CreatePlayerMonthLog(
        title=f"{context.missing_amount} silver short: "
        f"{unpaid_warriors} warrior{'' if unpaid_warriors == 1 else 's'} went unpaid.",
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
