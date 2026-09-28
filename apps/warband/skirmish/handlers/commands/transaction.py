import random

from queuebie import message_registry
from queuebie.messages import Event

from apps.warband.skirmish.messages.commands import transaction
from apps.warband.skirmish.messages.events.transaction import WarriorDroppedSilver

# What a fallen man leaves on the field, floored at nothing
DROPPED_SILVER_MU = 10
DROPPED_SILVER_SIGMA = 5


@message_registry.register_command(command=transaction.WarriorDropsSilver)
def handle_warrior_drops_silver(*, context: transaction.WarriorDropsSilver) -> list[Event] | Event:
    amount = round(max(random.gauss(DROPPED_SILVER_MU, DROPPED_SILVER_SIGMA), 0))

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
