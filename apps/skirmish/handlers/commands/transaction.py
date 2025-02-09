import random

from queuebie import message_registry
from queuebie.messages import Event

from apps.finance.models.transaction import Transaction
from apps.skirmish.messages.commands import transaction
from apps.skirmish.messages.events.transaction import WarriorDroppedSilver


@message_registry.register_command(command=transaction.WarriorDropsSilver)
def handle_warrior_drops_silver(*, context: transaction.WarriorDropsSilver) -> list[Event] | Event:
    amount = int(round(max(random.gauss(10, 5), 0)))

    if amount > 0:
        Transaction.objects.create_transaction(
            faction=context.gaining_faction, amount=amount, reason=f"Looted from {context.warrior}"
        )

        return [
            WarriorDroppedSilver(
                skirmish=context.skirmish,
                warrior=context.warrior,
                gaining_faction=context.gaining_faction,
                amount=amount,
            )
        ]

    return []
