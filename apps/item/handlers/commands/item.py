from apps.core.domain import message_registry
from apps.item.messages.commands import item
from apps.item.messages.events.item import ItemSold
from apps.item.models.item import Item


@message_registry.register_command(command=item.SellItem)
def handle_sell_item(context: item.SellItem.Context):
    # Remove ownership of item
    Item.objects.update_ownership(item=context.item, new_owner=None)

    return ItemSold.generator(
        context_data={
            "selling_faction": context.selling_faction,
            "item": context.item,
            "price": context.item.price,
        }
    )
