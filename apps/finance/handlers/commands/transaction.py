from queuebie import message_registry
from queuebie.messages import Event

from apps.finance.messages.commands.transaction import CreateTransaction
from apps.finance.messages.events.transaction import TransactionCreated
from apps.finance.models import Transaction


@message_registry.register_command(command=CreateTransaction)
def handle_create_transaction(*, context: CreateTransaction) -> list[Event] | Event:
    Transaction.objects.create_transaction(
        reason=context.reason,
        amount=context.amount,
        faction=context.faction,
        month=context.month,
    )

    return TransactionCreated(
        amount=context.amount,
        faction=context.faction,
        month=context.month,
    )
