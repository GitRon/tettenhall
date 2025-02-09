from dataclasses import dataclass

from queuebie.messages import Event

from apps.faction.models.faction import Faction
from apps.skirmish.models.skirmish import Skirmish
from apps.skirmish.models.warrior import Warrior


@dataclass(kw_only=True)
class WarriorAttackedWithDamage(Event):
    skirmish: Skirmish
    warrior: Warrior
    damage: int


@dataclass(kw_only=True)
class WarriorDefendedDamage(Event):
    skirmish: Skirmish
    warrior: Warrior
    damage: int


@dataclass(kw_only=True)
class WarriorTookDamage(Event):
    skirmish: Skirmish
    attacker: Warrior
    attacker_damage: int
    defender: Warrior
    defender_damage: int
    damage: int


@dataclass(kw_only=True)
class WarriorDefendedAllDamage(Event):
    skirmish: Skirmish
    attacker: Warrior
    attacker_damage: int
    defender: Warrior
    defender_damage: int


@dataclass(kw_only=True)
class WarriorWasIncapacitated(Event):
    skirmish: Skirmish
    warrior: Warrior
    by_warrior: Warrior


@dataclass(kw_only=True)
class WarriorHasFled(Event):
    skirmish: Skirmish
    warrior: Warrior


@dataclass(kw_only=True)
class WarriorWasKilled(Event):
    skirmish: Skirmish
    warrior: Warrior
    by_warrior: Warrior


@dataclass(kw_only=True)
class WarriorWasCaptured(Event):
    skirmish: Skirmish
    warrior: Warrior
    capturing_faction: Faction


@dataclass(kw_only=True)
class WarriorLostMorale(Event):
    skirmish: Skirmish
    warrior: Warrior
    lost_morale: int


@dataclass(kw_only=True)
class WarriorGainedMorale(Event):
    skirmish: Skirmish
    warrior: Warrior
    gained_morale: int


@dataclass(kw_only=True)
class WarriorGainedExperience(Event):
    skirmish: Skirmish
    warrior: Warrior
    gained_experience: int
