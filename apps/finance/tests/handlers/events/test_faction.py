from apps.faction.messages.events.faction import MonthlyBuildingMoneyEarned, NewFactionCreated
from apps.faction.tests.factories.faction import FactionFactory
from apps.finance.handlers.events.faction import (
    handle_building_money_earnings,
    handle_hand_out_starting_silver_for_new_factions,
)
from apps.finance.messages.commands.transaction import CreateTransaction


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
