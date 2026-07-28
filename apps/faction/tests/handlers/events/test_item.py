from apps.faction.handlers.events.item import handle_item_created_for_shop
from apps.faction.messages.commands.item import AddItemToTownShop
from apps.faction.tests.factories.faction import FactionFactory
from apps.item.messages.events import item
from apps.item.tests.factories.item import ItemFactory


def test_handle_item_created_for_shop_without_owner():
    faction = FactionFactory.build()
    new_item = ItemFactory.build()

    result = handle_item_created_for_shop(context=item.ItemCreated(owner=None, faction=faction, item=new_item, month=3))

    assert result == AddItemToTownShop(faction=faction, item=new_item, month=3)


def test_handle_item_created_for_shop_with_owner():
    faction = FactionFactory.build()
    new_item = ItemFactory.build(owner=faction)

    result = handle_item_created_for_shop(
        context=item.ItemCreated(owner=faction, faction=faction, item=new_item, month=3)
    )

    assert result is None
