from apps.faction.messages.events.faction import FactionFyrdReserveReplenished, MonthlyWarriorSalariesPaid
from apps.faction.tests.factories.faction import FactionFactory
from apps.month.handlers.events.faction import handle_faction_fyrd_reserve_replenished, handle_pay_monthly_salary
from apps.month.messages.commands.month import CreatePlayerMonthLog


def test_handle_faction_fyrd_reserve_replenished_logs_the_new_recruitees():
    faction = FactionFactory.build()

    result = handle_faction_fyrd_reserve_replenished(
        context=FactionFyrdReserveReplenished(faction=faction, new_recruitees=2, month=3)
    )

    assert result == CreatePlayerMonthLog(
        title="The fyrd has increased and has 2 new recruitees!", month=3, faction=faction
    )


def test_handle_pay_monthly_salary_logs_the_paid_amount():
    faction = FactionFactory.build()

    result = handle_pay_monthly_salary(context=MonthlyWarriorSalariesPaid(faction=faction, amount=250, month=3))

    assert result == CreatePlayerMonthLog(title="Monthly salaries paid of 250 silver.", month=3, faction=faction)
