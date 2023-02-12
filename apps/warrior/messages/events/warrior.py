from dataclasses import dataclass

from apps.core.event_loop.messages import Event
from apps.skirmish.models.warrior import Warrior


class WarriorMoraleReplenished(Event):
    @dataclass
    class Context:
        warrior: Warrior
        recovered_morale: int
        week: int


class WarriorHealthHealed(Event):
    @dataclass
    class Context:
        warrior: Warrior
        healed_points: int
        week: int
