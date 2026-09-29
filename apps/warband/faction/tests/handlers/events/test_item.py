from apps.warband.faction.handlers.events.item import (
    handle_hand_out_gear_for_changed_ownership,
    handle_item_created_for_shop,
)
from apps.warband.faction.messages.commands.item import AddItemToTownShop, HandOutFactionGear
from apps.warband.faction.tests.factories.faction import FactionFactory
from apps.warband.item.messages.events import item
from apps.warband.item.tests.factories.item import ItemFactory
from apps.warband.skirmish.tests.factories.warrior import WarriorFactory


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


def test_handle_hand_out_gear_for_changed_ownership_asks_the_new_owner():
    faction = FactionFactory.build()

    result = handle_hand_out_gear_for_changed_ownership(
        context=item.OwnershipChanged(
            previous_owner=WarriorFactory.build(), item=ItemFactory.build(), new_owner=faction
        )
    )

    assert result == HandOutFactionGear(faction=faction)
