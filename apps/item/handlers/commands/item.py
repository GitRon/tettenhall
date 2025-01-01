from apps.core.domain import message_registry
from apps.core.event_loop.messages import Event
from apps.item.messages.commands import item
from apps.item.messages.events.item import ItemBought, ItemSold
from apps.item.models.item import Item


@message_registry.register_command(command=item.SellItem)
def handle_sell_item(*, context: item.SellItem.Context) -> list[Event] | Event:
    # Remove ownership of item
    Item.objects.update_ownership(item=context.item, new_owner=None)

    return ItemSold(
        ItemSold.Context(
            selling_faction=context.selling_faction,
            item=context.item,
            price=context.item.price,
        )
    )


@message_registry.register_command(command=item.BuyItem)
def handle_buy_item(*, context: item.BuyItem.Context) -> list[Event] | Event:
    # Set new ownership of item
    Item.objects.update_ownership(item=context.item, new_owner=context.buying_faction)

    return ItemBought(
        ItemBought.Context(
            buying_faction=context.buying_faction,
            item=context.item,
            price=context.price,
        )
    )
