from queuebie import message_registry
from queuebie.messages import Command

from apps.finance.messages.commands.transaction import CreateTransaction
from apps.skirmish.messages.events import transaction


@message_registry.register_event(event=transaction.WarriorDroppedSilver)
def handle_faction_loots_warriors_silver(*, context: transaction.WarriorDroppedSilver) -> Command | None:
    return CreateTransaction(
        faction=context.gaining_faction,
        # Income, so positive: the faction is the one gaining the silver, not paying it. Every
        # negative amount in the ledger is a cost - wages, recruitment, purchases, building work.
        # The victor's own fallen are in this list too, so this also covers their purse coming back
        # to their faction, the same way their gear does
        amount=context.amount,
        reason=f"Looted from {context.warrior}",
        month=context.month,
    )
