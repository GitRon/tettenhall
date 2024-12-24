from apps.core.domain import message_registry
from apps.item.messages.events import item
from apps.marketplace.models.marketplace import Marketplace


@message_registry.register_event(event=item.ItemSold)
def handle_add_sold_item_to_marketplace(*, context: item.ItemSold.Context):
    marketplace = Marketplace.objects.all().first()
    marketplace.available_items.add(context.item)
