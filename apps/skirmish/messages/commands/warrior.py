from dataclasses import dataclass

from queuebie.messages import Command

from apps.faction.models.faction import Faction
from apps.skirmish.models.skirmish import Skirmish
from apps.skirmish.models.warrior import Warrior


@dataclass(kw_only=True)
class StoreLastUsedSkirmishAction(Command):
    skirmish: Skirmish
    warrior: Warrior
    skirmish_action: int


@dataclass(kw_only=True)
class CaptureWarrior(Command):
    skirmish: Skirmish
    warrior: Warrior
    capturing_faction: Faction


@dataclass(kw_only=True)
class ReduceHealth(Command):
    skirmish: Skirmish
    warrior: Warrior
    attacker: Warrior
    lost_health: int


@dataclass(kw_only=True)
class ReduceMorale(Command):
    skirmish: Skirmish
    warrior: Warrior
    lost_morale: int


@dataclass(kw_only=True)
class ReduceMoraleOfRemainingWarriors(Command):
    skirmish: Skirmish
    warrior: Warrior


@dataclass(kw_only=True)
class IncreaseMorale(Command):
    skirmish: Skirmish
    warrior: Warrior
    increased_morale: int


@dataclass(kw_only=True)
class IncreaseExperience(Command):
    skirmish: Skirmish
    warrior: Warrior
    # An int, because a fractional gain would put the level thresholds off by a rounding error
    increased_experience: int


@dataclass(kw_only=True)
class IncreaseWarriorStatsOnLevelUp(Command):
    skirmish: Skirmish
    warrior: Warrior
