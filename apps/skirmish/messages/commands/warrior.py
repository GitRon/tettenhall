from dataclasses import dataclass

from apps.core.event_loop.messages import Command
from apps.faction.models.faction import Faction
from apps.skirmish.models.skirmish import Skirmish
from apps.skirmish.models.warrior import Warrior


class CaptureWarrior(Command):
    @dataclass(kw_only=True)
    class Context:
        skirmish: Skirmish
        warrior: Warrior
        capturing_faction: Faction


class ReduceMorale(Command):
    @dataclass(kw_only=True)
    class Context:
        skirmish: Skirmish
        warrior: Warrior
        lost_morale: int


class IncreaseMorale(Command):
    @dataclass(kw_only=True)
    class Context:
        skirmish: Skirmish
        warrior: Warrior
        increased_morale: float


class IncreaseExperience(Command):
    @dataclass(kw_only=True)
    class Context:
        skirmish: Skirmish
        warrior: Warrior
        increased_experience: int
