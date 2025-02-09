from queuebie import message_registry

from apps.marketplace.messages.events.item import MarketplaceItemsRestocked
from apps.month.models.player_month_log import PlayerMonthLog


@message_registry.register_event(event=MarketplaceItemsRestocked)
def handle_marketplace_items_restocked(*, context: MarketplaceItemsRestocked):
    PlayerMonthLog.objects.create_record(
        title=f"Marketplace {context.marketplace.town_name} has new stock!",
        month=context.month,
        faction_id=context.marketplace.savegame.player_faction_id,
    )
