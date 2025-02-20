from dataclasses import dataclass

from queuebie.messages import Command

from apps.faction.models import Faction


@dataclass(kw_only=True)
class CreateTransaction(Command):
    reason: str
    amount: int
    faction: Faction
    month: int
