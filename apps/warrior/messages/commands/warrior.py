from dataclasses import dataclass

from queuebie.messages import Command

from apps.faction.models.faction import Faction
from apps.skirmish.models.warrior import Warrior


@dataclass(kw_only=True)
class ReplenishWarriorMorale(Command):
    warrior: Warrior
    month: int


@dataclass(kw_only=True)
class HealInjuredWarrior(Command):
    warrior: Warrior
    month: int


@dataclass(kw_only=True)
class RecruitCapturedWarrior(Command):
    warrior: Warrior
    faction: Faction


@dataclass(kw_only=True)
class EnslaveCapturedWarrior(Command):
    warrior: Warrior
    faction: Faction
