from queuebie import message_registry

from apps.marketplace.messages.events.item import MarketplaceItemsRestocked
from apps.week.models.player_week_log import PlayerWeekLog


@message_registry.register_event(event=MarketplaceItemsRestocked)
def handle_marketplace_items_restocked(*, context: MarketplaceItemsRestocked):
    PlayerWeekLog.objects.create_record(
        title=f"Marketplace {context.marketplace.town_name} has new stock!",
        week=context.week,
        faction_id=context.marketplace.savegame.player_faction_id,
    )
