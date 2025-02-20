from queuebie import message_registry
from queuebie.messages import Command

from apps.finance.messages.commands.transaction import CreateTransaction
from apps.skirmish.messages.events import transaction


@message_registry.register_event(event=transaction.WarriorDroppedSilver)
def handle_faction_loots_warriors_silver(*, context: transaction.WarriorDroppedSilver) -> Command | None:
    return CreateTransaction(
        faction=context.gaining_faction,
        amount=-context.amount,
        reason=f"Looted from {context.warrior}",
        month=context.month,
    )
