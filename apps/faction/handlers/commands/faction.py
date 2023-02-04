import random

from apps.core.domain import message_registry
from apps.faction.messages.commands.faction import ReplenishFyrdReserve
from apps.faction.messages.events.faction import FactionFyrdReserveReplenished
from apps.faction.models.faction import Faction


@message_registry.register_command(command=ReplenishFyrdReserve)
def handle_replenish_fyrd_reserve(context: ReplenishFyrdReserve.Context):
    new_recruitees = random.randrange(0, 3)

    if new_recruitees == 0:
        return

    # Update faction
    Faction.objects.replenish_fyrd_reserve(faction=context.faction, new_recruitees=new_recruitees)

    return FactionFyrdReserveReplenished.generator(
        context_data={
            "faction": context.faction,
            "new_recruitees": new_recruitees,
            "week": context.week,
        }
    )
