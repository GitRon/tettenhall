from queuebie import message_registry
from queuebie.messages import Command

from apps.warband.faction.messages.commands.item import (
    AddItemToTownShop,
    HandOutFactionGear,
    RemoveItemFromTownShop,
    RestockTownShopItems,
)
from apps.warband.faction.messages.events.faction import FactionMonthPlanned, NewFactionCreated
from apps.warband.faction.messages.events.item import ShopItemPurchaseApproved
from apps.warband.item.messages.commands.item import BuyItem
from apps.warband.item.messages.events import item


@message_registry.register_event(event=item.ItemCreated)
def handle_item_created_for_shop(*, context: item.ItemCreated) -> Command | None:
    if context.owner is None:
        return AddItemToTownShop(faction=context.faction, item=context.item, month=context.month)

    return None


@message_registry.register_event(event=item.ItemSold)
def handle_add_sold_item_to_shop(*, context: item.ItemSold) -> Command:
    return AddItemToTownShop(faction=context.selling_faction, item=context.item, month=context.month)


@message_registry.register_event(event=item.ItemBought)
def handle_remove_bought_item_from_shop(*, context: item.ItemBought) -> Command:
    return RemoveItemFromTownShop(faction=context.buying_faction, item=context.item, month=context.month)


@message_registry.register_event(event=NewFactionCreated)
def handle_stock_items_in_shop_for_new_faction(*, context: NewFactionCreated) -> Command:
    return RestockTownShopItems(faction=context.faction, month=context.current_month)


@message_registry.register_event(event=FactionMonthPlanned)
def handle_restock_items_in_shop_once_month_is_planned(*, context: FactionMonthPlanned) -> Command:
    # Once the month's buying is done rather than when it opens, so a rival weighs the shelf that stood
    # all month before it is replaced - the pub's restock hangs off the same event for the same reason
    return RestockTownShopItems(faction=context.faction, month=context.month)


@message_registry.register_event(event=ShopItemPurchaseApproved)
def handle_buy_item_for_approved_shop_purchase(*, context: ShopItemPurchaseApproved) -> Command:
    # Pure mapping, because handle_plan_faction_month already weighed the whole decision. That is what
    # lets a rival buy through the same command the player's shop dispatches.
    return BuyItem(buying_faction=context.faction, price=context.item.price, item=context.item, month=context.month)


@message_registry.register_event(event=item.OwnershipChanged)
def handle_hand_out_gear_for_changed_ownership(*, context: item.OwnershipChanged) -> Command:
    # The spoils of a fight land in the victor's stores one item at a time, and whether any of them
    # beats what its men carry is the hand-out's question - which also refuses the player
    return HandOutFactionGear(faction=context.new_owner)


@message_registry.register_event(event=item.ItemBought)
def handle_hand_out_gear_for_bought_item(*, context: item.ItemBought) -> Command:
    # A purchase lands in the stores like the spoils of a fight, and the hand-out refuses the player here too
    return HandOutFactionGear(faction=context.buying_faction)
