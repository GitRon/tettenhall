from apps.faction.messages.events.faction import (
    FactionFyrdReserveReplenished,
    MonthlyBuildingMoneyEarned,
    MonthlyWarriorSalariesPaid,
)
from apps.faction.tests.factories.faction import FactionFactory
from apps.month.handlers.events.faction import (
    handle_faction_fyrd_reserve_replenished,
    handle_monthly_building_earnings,
    handle_pay_monthly_salary,
)
from apps.month.messages.commands.month import CreatePlayerMonthLog


def test_handle_faction_fyrd_reserve_replenished_logs_the_new_recruitees():
    faction = FactionFactory.build()

    result = handle_faction_fyrd_reserve_replenished(
        context=FactionFyrdReserveReplenished(faction=faction, new_recruitees=2, month=3)
    )

    assert result == CreatePlayerMonthLog(title="The fyrd has grown by 2 new recruitees!", month=3, faction=faction)


def test_handle_faction_fyrd_reserve_replenished_keeps_a_single_recruitee_singular():
    faction = FactionFactory.build()

    result = handle_faction_fyrd_reserve_replenished(
        context=FactionFyrdReserveReplenished(faction=faction, new_recruitees=1, month=3)
    )

    assert result == CreatePlayerMonthLog(title="The fyrd has grown by 1 new recruitee!", month=3, faction=faction)


def test_handle_pay_monthly_salary_logs_the_paid_amount():
    faction = FactionFactory.build()

    result = handle_pay_monthly_salary(context=MonthlyWarriorSalariesPaid(faction=faction, amount=250, month=3))

    assert result == CreatePlayerMonthLog(title="Monthly salaries of 250 silver paid.", month=3, faction=faction)


def test_handle_monthly_building_earnings_logs_the_earned_amount():
    faction = FactionFactory.build()

    result = handle_monthly_building_earnings(context=MonthlyBuildingMoneyEarned(faction=faction, amount=300, month=3))

    assert result == CreatePlayerMonthLog(title="Buildings earned 300 silver this month.", month=3, faction=faction)
