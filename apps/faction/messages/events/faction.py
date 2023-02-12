from dataclasses import dataclass

from apps.core.event_loop.messages import Event
from apps.faction.models.faction import Faction
from apps.skirmish.models.warrior import Warrior


class FactionFyrdReserveReplenished(Event):
    @dataclass
    class Context:
        faction: Faction
        new_recruitees: int
        week: int


class WeeklyWarriorSalariesPaid(Event):
    @dataclass
    class Context:
        faction: Faction
        amount: int
        week: int


class FactionWarriorsWithLowMoraleDetermined(Event):
    @dataclass
    class Context:
        faction: Faction
        warrior_list: list[Warrior]
        week: int
