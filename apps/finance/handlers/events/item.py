from queuebie import message_registry
from queuebie.messages import Command

from apps.finance.messages.commands.transaction import CreateTransaction
from apps.item.messages.events import item


@message_registry.register_event(event=item.ItemSold)
def handle_item_sold(*, context: item.ItemSold) -> Command:
    # Give out the money
    return CreateTransaction(
        reason=f"{context.item_name} sold",
        amount=context.price,
        faction=context.selling_faction,
        month=context.month,
    )


@message_registry.register_event(event=item.ItemBought)
def handle_item_bought(*, context: item.ItemBought) -> Command:
    # Pay for item
    return CreateTransaction(
        reason=f"{context.item_name} bought",
        amount=-context.price,
        faction=context.buying_faction,
        month=context.month,
    )
