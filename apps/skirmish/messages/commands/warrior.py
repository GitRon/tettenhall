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
    """
    Take a warrior prisoner.

    "skirmish" is nullable and carries no default on purpose: a man is taken off the field of a fight
    or seized in an occupied town, and every call site says which. A default would let a new one
    forget, and the fight it belongs to would go missing from the battle log without a word.
    """

    skirmish: Skirmish | None
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
