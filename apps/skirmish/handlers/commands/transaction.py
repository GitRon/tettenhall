import random

from apps.core.domain import message_registry
from apps.finance.models.transaction import Transaction
from apps.skirmish.messages.commands import transaction
from apps.skirmish.messages.events.transaction import WarriorDroppedSilver


@message_registry.register_command(command=transaction.WarriorDropsSilver)
def handle_warrior_drops_silver(context: transaction.WarriorDropsSilver.Context) -> list:
    amount = int(round(max(random.gauss(10, 5), 0)))

    if amount > 0:
        Transaction.objects.create(
            faction=context.gaining_faction, amount=amount, reason=f"Looted from {context.warrior}"
        )

        return WarriorDroppedSilver.generator(
            context_data={
                "skirmish": context.skirmish,
                "warrior": context.warrior,
                "gaining_faction": context.gaining_faction,
                "amount": amount,
            }
        )
