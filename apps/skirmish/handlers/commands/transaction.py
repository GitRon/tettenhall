import random

from queuebie import message_registry
from queuebie.messages import Event

from apps.skirmish.messages.commands import transaction
from apps.skirmish.messages.events.transaction import WarriorDroppedSilver


@message_registry.register_command(command=transaction.WarriorDropsSilver)
def handle_warrior_drops_silver(*, context: transaction.WarriorDropsSilver) -> list[Event] | Event:
    amount = round(max(random.gauss(10, 5), 0))

    if amount > 0:
        return [
            WarriorDroppedSilver(
                skirmish=context.skirmish,
                warrior=context.warrior,
                gaining_faction=context.gaining_faction,
                amount=amount,
                month=context.month,
            )
        ]

    return []
