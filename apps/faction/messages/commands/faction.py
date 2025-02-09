from dataclasses import dataclass

from queuebie.messages import Command

from apps.faction.models.faction import Faction


@dataclass(kw_only=True)
class ReplenishFyrdReserve(Command):
    faction: Faction
    week: int


@dataclass(kw_only=True)
class PayWeeklyWarriorSalaries(Command):
    faction: Faction
    week: int


@dataclass(kw_only=True)
class DetermineWarriorsWithLowMorale(Command):
    faction: Faction
    week: int


@dataclass(kw_only=True)
class DetermineInjuredWarriors(Command):
    faction: Faction
    week: int
