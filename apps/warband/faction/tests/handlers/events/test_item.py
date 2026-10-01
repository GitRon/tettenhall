from apps.warband.faction.handlers.events.item import (
    handle_buy_item_for_approved_shop_purchase,
    handle_hand_out_gear_for_bought_item,
    handle_hand_out_gear_for_changed_ownership,
    handle_item_created_for_shop,
    handle_restock_items_in_shop_once_month_is_planned,
    handle_stock_items_in_shop_for_new_faction,
)
from apps.warband.faction.messages.commands.item import AddItemToTownShop, HandOutFactionGear, RestockTownShopItems
from apps.warband.faction.messages.events.faction import FactionMonthPlanned, NewFactionCreated
from apps.warband.faction.messages.events.item import ShopItemPurchaseApproved
from apps.warband.faction.tests.factories.faction import FactionFactory
from apps.warband.item.messages.commands.item import BuyItem
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


def test_handle_stock_items_in_shop_for_new_faction_maps_to_command():
    faction = FactionFactory.build()

    result = handle_stock_items_in_shop_for_new_faction(
        context=NewFactionCreated(faction=faction, current_month=1, is_player=False)
    )

    assert result == RestockTownShopItems(faction=faction, month=1)


def test_handle_restock_items_in_shop_once_month_is_planned_maps_to_command():
    faction = FactionFactory.build()

    result = handle_restock_items_in_shop_once_month_is_planned(context=FactionMonthPlanned(faction=faction, month=7))

    assert result == RestockTownShopItems(faction=faction, month=7)


def test_handle_buy_item_for_approved_shop_purchase_buys_at_the_list_price():
    faction = FactionFactory.build()
    sword = ItemFactory.build(price=80)

    result = handle_buy_item_for_approved_shop_purchase(
        context=ShopItemPurchaseApproved(faction=faction, item=sword, month=4)
    )

    assert result == BuyItem(buying_faction=faction, price=80, item=sword, month=4)


def test_handle_hand_out_gear_for_bought_item_asks_the_buyer():
    faction = FactionFactory.build()

    result = handle_hand_out_gear_for_bought_item(
        context=item.ItemBought(buying_faction=faction, item=ItemFactory.build(), item_name="Sword", price=80, month=4)
    )

    assert result == HandOutFactionGear(faction=faction)
