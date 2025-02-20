from dataclasses import dataclass

from queuebie.messages import Event

from apps.faction.models.faction import Faction


@dataclass(kw_only=True)
class TransactionCreated(Event):
    amount: int
    faction: Faction
    month: int
