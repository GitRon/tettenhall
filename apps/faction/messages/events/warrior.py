from dataclasses import dataclass

from apps.core.event_loop.messages import Event
from apps.faction.models.faction import Faction
from apps.skirmish.models.warrior import Warrior


class WarriorWasDraftedFromFyrd(Event):
    @dataclass
    class Context:
        faction: Faction
        warrior: Warrior
