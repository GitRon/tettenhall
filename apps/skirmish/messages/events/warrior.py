from dataclasses import dataclass

from queuebie.messages import Event

from apps.faction.models.faction import Faction
from apps.skirmish.choices.skirmish_action import SkirmishActionTypeHint
from apps.skirmish.models.skirmish import Skirmish
from apps.skirmish.models.warrior import Warrior


@dataclass(kw_only=True)
class LastUsedSkirmishActionStored(Event):
    skirmish: Skirmish
    warrior: Warrior
    skirmish_action: int


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
    # Carried because turning a blow aside and simply standing there behind a shield are worth
    # opposite things to a warrior's nerve, and the damage alone cannot tell them apart
    defender_action: SkirmishActionTypeHint


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


@dataclass(kw_only=True)
class WarriorGainedLevel(Event):
    skirmish: Skirmish
    warrior: Warrior
    level: int


@dataclass(kw_only=True)
class WarriorImprovedStats(Event):
    skirmish: Skirmish
    warrior: Warrior
    gained_strength: int
    gained_dexterity: int
    gained_max_health: int
    gained_max_morale: int
    gained_salary: int
    # The wage *after* the growth, carried rather than read back off the warrior when the log line is
    # written. Every message in a level-up chain holds the same instance, so a gain crossing two
    # thresholds grows it twice before either log handler runs - and both lines would then quote the
    # wage the second growth left behind.
    new_monthly_salary: int
