from dataclasses import dataclass

from queuebie.messages import Event

from apps.skirmish.models.warrior import Warrior


@dataclass(kw_only=True)
class WarriorMoraleReplenished(Event):
    warrior: Warrior
    recovered_morale: int
    week: int


@dataclass(kw_only=True)
class WarriorHealthHealed(Event):
    warrior: Warrior
    healed_points: int
    week: int
