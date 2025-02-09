from dataclasses import dataclass

from queuebie.messages import Event

from apps.faction.models.faction import Faction
from apps.skirmish.models.warrior import Warrior


@dataclass(kw_only=True)
class FactionFyrdReserveReplenished(Event):
    faction: Faction
    new_recruitees: int
    week: int


@dataclass(kw_only=True)
class WeeklyWarriorSalariesPaid(Event):
    faction: Faction
    amount: int
    week: int


@dataclass(kw_only=True)
class FactionWarriorsWithLowMoraleDetermined(Event):
    faction: Faction
    warrior_list: list[Warrior]
    week: int
