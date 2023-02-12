from dataclasses import dataclass

from apps.core.event_loop.messages import Command
from apps.faction.models.faction import Faction


class ReplenishFyrdReserve(Command):
    @dataclass
    class Context:
        faction: Faction
        week: int


class PayWeeklyWarriorSalaries(Command):
    @dataclass
    class Context:
        faction: Faction
        week: int


class DetermineWarriorsWithLowMorale(Command):
    @dataclass
    class Context:
        faction: Faction
        week: int


class DetermineInjuredWarriors(Command):
    @dataclass
    class Context:
        faction: Faction
        week: int
