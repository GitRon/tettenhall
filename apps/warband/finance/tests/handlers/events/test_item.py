from apps.warband.faction.tests.factories.faction import FactionFactory
from apps.warband.finance.handlers.events.item import handle_item_upgraded
from apps.warband.finance.messages.commands.transaction import CreateTransaction
from apps.warband.item.messages.events.item import ItemUpgraded
from apps.warband.item.tests.factories.item import ItemFactory


def test_handle_item_upgraded_charges_the_faction_for_the_rework():
    faction = FactionFactory.build()
    context = ItemUpgraded(faction=faction, item=ItemFactory.build(), item_name="Rusty Sax", costs=40, month=4)

    result = handle_item_upgraded(context=context)

    assert result == CreateTransaction(faction=faction, amount=-40, reason="Rusty Sax reforged", month=4)
