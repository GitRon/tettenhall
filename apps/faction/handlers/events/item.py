from queuebie import message_registry
from queuebie.messages import Command

from apps.faction.messages.commands.faction import AddItemToTownShop, RestockTownShopItems
from apps.faction.messages.events.faction import NewFactionCreated
from apps.item.messages.events import item
from apps.month.messages.events.month import MonthPrepared


@message_registry.register_event(event=item.ItemCreated)
def handle_item_created_for_shop(*, context: item.ItemCreated) -> Command | None:
    if context.owner is None:
        return AddItemToTownShop(faction=context.faction, item=context.item, month=context.month)

    return None


@message_registry.register_event(event=item.ItemSold)
def handle_add_sold_item_to_marketplace(*, context: item.ItemSold) -> Command:
    context.selling_faction.available_items.add(context.item)
    # TODO: this is wrong. we need a command for the change.


@message_registry.register_event(event=item.ItemBought)
def handle_remove_bought_item_from_marketplace(*, context: item.ItemBought) -> Command:
    context.buying_faction.available_items.remove(context.item)
    # TODO: this is wrong. we need a command for the change.


@message_registry.register_event(event=NewFactionCreated)
@message_registry.register_event(event=MonthPrepared)
def handle_restock_items_in_marketplace_for_new_month(*, context: MonthPrepared | NewFactionCreated) -> Command:
    return RestockTownShopItems(faction=context.faction, month=context.current_month)
