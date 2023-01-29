from apps.core.domain import message_registry
from apps.marketplace.messages.events.item import MarketplaceItemsRestocked
from apps.week.models.player_week_log import PlayerWeekLog


@message_registry.register_event(event=MarketplaceItemsRestocked)
def handle_marketplace_items_restocked(context: MarketplaceItemsRestocked.Context):
    PlayerWeekLog.objects.create_record(
        title=f"Marketplace {context.marketplace.town_name} has new stock!",
        message="Some fancy text",
        week=context.week,
    )
