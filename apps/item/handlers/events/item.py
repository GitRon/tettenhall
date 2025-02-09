from queuebie import message_registry

from apps.finance.models.transaction import Transaction
from apps.item.messages.events import item


@message_registry.register_event(event=item.ItemSold)
def handle_item_sold(*, context: item.ItemSold):
    # Give out the money
    Transaction.objects.create_transaction(
        reason=f"{context.item} sold", amount=context.price, faction=context.selling_faction
    )


@message_registry.register_event(event=item.ItemBought)
def handle_item_bought(*, context: item.ItemBought):
    # Pay for item
    Transaction.objects.create_transaction(
        reason=f"{context.item} bought",
        amount=-context.price,
        faction=context.buying_faction,
    )
