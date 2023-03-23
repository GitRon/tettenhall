from apps.core.domain import message_registry
from apps.finance.models.transaction import Transaction
from apps.item.messages.events import item


@message_registry.register_event(event=item.ItemSold)
def handle_item_sold(context: item.ItemSold.Context):
    # Give out the money
    Transaction.objects.create_transaction(
        reason=f"{context.item} sold", amount=context.price, faction=context.selling_faction
    )
