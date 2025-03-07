from dataclasses import dataclass

from queuebie.messages import Command

from apps.faction.models import Culture
from apps.faction.models.faction import Faction
from apps.skirmish.models.warrior import Warrior
from apps.warrior.services.generators.warrior.base import BaseWarriorGenerator


@dataclass(kw_only=True)
class CreateWarrior(Command):
    faction: Faction
    culture: Culture
    generator_class: type[BaseWarriorGenerator]
    month: int


@dataclass(kw_only=True)
class CreateNewLeaderWarrior(Command):
    # TODO: entweder mach ich alle so oder ich nutze hier das generische event mit generator_class?
    faction: Faction


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
    month: int


@dataclass(kw_only=True)
class EnslaveCapturedWarrior(Command):
    warrior: Warrior
    faction: Faction
    month: int
