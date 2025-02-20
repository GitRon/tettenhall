from dataclasses import dataclass

from queuebie.messages import Event

from apps.faction.models.faction import Faction
from apps.skirmish.models.skirmish import Skirmish
from apps.skirmish.models.warrior import Warrior


@dataclass(kw_only=True)
class WarriorDroppedSilver(Event):
    skirmish: Skirmish
    warrior: Warrior
    gaining_faction: Faction
    amount: int
    month: int
