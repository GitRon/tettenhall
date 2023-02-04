from dataclasses import dataclass

from apps.core.event_loop.messages import Event
from apps.faction.models.faction import Faction


class FactionFyrdReserveReplenished(Event):
    @dataclass
    class Context:
        faction: Faction
        new_recruitees: int
        week: int
