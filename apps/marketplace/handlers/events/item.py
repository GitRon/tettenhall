from queuebie import message_registry
from queuebie.messages import Command

from apps.faction.messages.events.faction import NewFactionCreated
from apps.item.messages.events import item
from apps.marketplace.messages.commands.item import RestockMarketplaceItems
from apps.month.messages.events.month import MonthPrepared


@message_registry.register_event(event=item.ItemSold)
def handle_add_sold_item_to_marketplace(*, context: item.ItemSold):
    marketplace = context.item.savegame.marketplace
    marketplace.available_items.add(context.item)


@message_registry.register_event(event=item.ItemBought)
def handle_remove_bought_item_from_marketplace(*, context: item.ItemBought):
    marketplace = context.item.savegame.marketplace
    marketplace.available_items.remove(context.item)


@message_registry.register_event(event=NewFactionCreated)
@message_registry.register_event(event=MonthPrepared)
def handle_restock_items_in_marketplace_for_new_month(*, context: MonthPrepared | NewFactionCreated) -> list[Command]:
    return [RestockMarketplaceItems(marketplace=context.marketplace, month=context.current_month)]
