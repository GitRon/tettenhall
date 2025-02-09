from dataclasses import dataclass

from queuebie.messages import Command

from apps.faction.models.faction import Faction
from apps.skirmish.models.skirmish import Skirmish
from apps.skirmish.models.warrior import Warrior


@dataclass(kw_only=True)
class CaptureWarrior(Command):
    skirmish: Skirmish
    warrior: Warrior
    capturing_faction: Faction


@dataclass(kw_only=True)
class ReduceMorale(Command):
    skirmish: Skirmish
    warrior: Warrior
    lost_morale: float


@dataclass(kw_only=True)
class IncreaseMorale(Command):
    skirmish: Skirmish
    warrior: Warrior
    increased_morale: float


@dataclass(kw_only=True)
class IncreaseExperience(Command):
    skirmish: Skirmish
    warrior: Warrior
    increased_experience: float
