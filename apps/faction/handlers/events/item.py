from queuebie import message_registry
from queuebie.messages import Command

from apps.faction.messages.commands.faction import RestockTownShopItems
from apps.faction.messages.commands.item import AddItemToTownShop, RemoveItemFromTownShop
from apps.faction.messages.events.faction import NewFactionCreated
from apps.item.messages.events import item
from apps.month.messages.events.month import MonthPrepared


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
@message_registry.register_event(event=MonthPrepared)
def handle_restock_items_in_shop_for_new_month(*, context: MonthPrepared | NewFactionCreated) -> Command:
    return RestockTownShopItems(faction=context.faction, month=context.current_month)
