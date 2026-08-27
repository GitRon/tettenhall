from apps.faction.messages.events.faction import (
    MonthlyBuildingMoneyEarned,
    MonthlyFactionIncomeEarned,
    MonthlyWarriorSalariesPaid,
    NewFactionCreated,
)
from apps.faction.messages.events.warrior import WarriorRecruited
from apps.faction.tests.factories.faction import FactionFactory
from apps.finance.handlers.events.faction import (
    handle_building_money_earnings,
    handle_hand_out_starting_silver_for_new_factions,
    handle_monthly_faction_income,
    handle_pay_warrior_salaries,
    handle_warrior_recruited,
)
from apps.finance.messages.commands.transaction import CreateTransaction
from apps.skirmish.tests.factories.warrior import WarriorFactory


def test_handle_warrior_recruited_debits_the_recruitment_price():
    faction = FactionFactory.build()
    warrior = WarriorFactory.build(faction=faction)

    result = handle_warrior_recruited(
        context=WarriorRecruited(faction=faction, warrior=warrior, recruitment_price=300, month=3)
    )

    assert result == CreateTransaction(faction=faction, amount=-300, reason=f"{warrior} recruited", month=3)


def test_handle_warrior_recruited_writes_nothing_for_a_free_draft():
    """
    A levy called up out of the fyrd costs nothing, and a row reading "-0 silver" is not a payment.
    Every faction drafts every month it can, so those rows would bury the ledger they sit in.
    """
    faction = FactionFactory.build()

    result = handle_warrior_recruited(
        context=WarriorRecruited(
            faction=faction, warrior=WarriorFactory.build(faction=faction), recruitment_price=0, month=3
        )
    )

    assert result is None


def test_handle_pay_warrior_salaries_debits_what_was_actually_paid():
    """
    The amount is what the faction managed to pay, not what it owed - a purse that covered three of
    five men is only ever charged for the three.
    """
    faction = FactionFactory.build()

    result = handle_pay_warrior_salaries(context=MonthlyWarriorSalariesPaid(faction=faction, amount=250, month=3))

    assert result == CreateTransaction(faction=faction, amount=-250, reason="Salaries paid in month 3.", month=3)


def test_handle_building_money_earnings_credits_the_faction():
    faction = FactionFactory.build()

    result = handle_building_money_earnings(context=MonthlyBuildingMoneyEarned(faction=faction, amount=300, month=3))

    assert result == CreateTransaction(faction=faction, amount=300, reason="Building earnings in month 3.", month=3)


def test_handle_hand_out_starting_silver_for_new_factions_credits_the_starting_purse():
    faction = FactionFactory.build()

    result = handle_hand_out_starting_silver_for_new_factions(
        context=NewFactionCreated(faction=faction, current_month=1)
    )

    assert result == CreateTransaction(faction=faction, amount=1000, reason="Starting silver", month=1)


def test_handle_monthly_faction_income_credits_the_faction():
    """
    Its own line rather than the building one: a rival has no buildings to have earned it with.
    """
    faction = FactionFactory.build()

    result = handle_monthly_faction_income(context=MonthlyFactionIncomeEarned(faction=faction, amount=450, month=3))

    assert result == CreateTransaction(faction=faction, amount=450, reason="Faction income in month 3.", month=3)
