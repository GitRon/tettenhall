from dataclasses import dataclass

from apps.core.event_loop.messages import Command
from apps.faction.models.faction import Faction


class ReplenishFyrdReserve(Command):
    @dataclass(kw_only=True)
    class Context:
        faction: Faction
        week: int


class PayWeeklyWarriorSalaries(Command):
    @dataclass(kw_only=True)
    class Context:
        faction: Faction
        week: int


class DetermineWarriorsWithLowMorale(Command):
    @dataclass(kw_only=True)
    class Context:
        faction: Faction
        week: int


class DetermineInjuredWarriors(Command):
    @dataclass(kw_only=True)
    class Context:
        faction: Faction
        week: int
