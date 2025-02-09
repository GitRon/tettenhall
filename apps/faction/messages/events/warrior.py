from dataclasses import dataclass

from queuebie.messages import Event

from apps.faction.models.faction import Faction
from apps.skirmish.models.warrior import Warrior


@dataclass(kw_only=True)
class WarriorRecruited(Event):
    warrior: Warrior
    faction: Faction
    recruitment_price: int


@dataclass(kw_only=True)
class WarriorWasSoldIntoSlavery(Event):
    # TODO: refactor all "sell X" event and pass generic context string for transaction title
    warrior: Warrior
    selling_faction: Faction
    price: int
