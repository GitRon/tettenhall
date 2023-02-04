from dataclasses import dataclass

from apps.core.event_loop.messages import Command
from apps.faction.models.faction import Faction


class ReplenishFyrdReserve(Command):
    @dataclass
    class Context:
        faction: Faction
        week: int
