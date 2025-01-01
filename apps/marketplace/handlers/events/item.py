from apps.core.domain import message_registry
from apps.core.event_loop.messages import Command
from apps.item.messages.events import item
from apps.marketplace.messages.commands.item import RestockMarketplaceItems
from apps.marketplace.models.marketplace import Marketplace
from apps.week.messages.events.week import WeekPrepared


@message_registry.register_event(event=item.ItemSold)
def handle_add_sold_item_to_marketplace(*, context: item.ItemSold.Context):
    # TODO: multi-tenancy -> items need a FK to savegame
    marketplace = Marketplace.objects.all().first()
    marketplace.available_items.add(context.item)


@message_registry.register_event(event=item.ItemBought)
def handle_remove_bought_item_from_marketplace(*, context: item.ItemBought.Context):
    # TODO: multi-tenancy -> items need a FK to savegame
    marketplace = Marketplace.objects.all().first()
    marketplace.available_items.remove(context.item)


@message_registry.register_event(event=WeekPrepared)
def handle_restock_items_in_marketplace_for_new_week(*, context: WeekPrepared.Context) -> list[Command]:
    return [
        RestockMarketplaceItems(
            RestockMarketplaceItems.Context(marketplace=context.marketplace, week=context.current_week)
        )
    ]
