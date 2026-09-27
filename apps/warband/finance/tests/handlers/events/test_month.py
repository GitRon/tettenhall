from apps.warband.faction.tests.factories.faction import FactionFactory
from apps.warband.finance.handlers.events.month import handle_bring_in_harvest_for_new_month
from apps.warband.finance.messages.commands.transaction import CreateTransaction
from apps.warband.month.messages.events.month import FactionMonthPrepared


def test_handle_bring_in_harvest_for_new_month_in_haligmonath():
    """Month 6 is Haligmonath."""
    faction = FactionFactory.build()

    result = handle_bring_in_harvest_for_new_month(context=FactionMonthPrepared(faction=faction, current_month=6))

    assert result == CreateTransaction(faction=faction, amount=100, reason="Harvest", month=6)


def test_handle_bring_in_harvest_for_new_month_outside_the_harvest():
    result = handle_bring_in_harvest_for_new_month(
        context=FactionMonthPrepared(faction=FactionFactory.build(), current_month=5)
    )

    assert result is None
