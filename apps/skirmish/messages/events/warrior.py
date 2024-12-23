from dataclasses import dataclass

from apps.core.event_loop.messages import Event
from apps.faction.models.faction import Faction
from apps.skirmish.models.skirmish import Skirmish
from apps.skirmish.models.warrior import Warrior


class WarriorAttackedWithDamage(Event):
    @dataclass(kw_only=True)
    class Context:
        skirmish: Skirmish
        warrior: Warrior
        damage: int


class WarriorDefendedDamage(Event):
    @dataclass(kw_only=True)
    class Context:
        skirmish: Skirmish
        warrior: Warrior
        damage: int


class WarriorTookDamage(Event):
    @dataclass(kw_only=True)
    class Context:
        skirmish: Skirmish
        attacker: Warrior
        attacker_damage: int
        defender: Warrior
        defender_damage: int
        damage: int


class WarriorDefendedAllDamage(Event):
    @dataclass(kw_only=True)
    class Context:
        skirmish: Skirmish
        attacker: Warrior
        attacker_damage: int
        defender: Warrior
        defender_damage: int


class WarriorWasIncapacitated(Event):
    @dataclass(kw_only=True)
    class Context:
        skirmish: Skirmish
        warrior: Warrior
        by_warrior: Warrior


class WarriorHasFled(Event):
    @dataclass(kw_only=True)
    class Context:
        skirmish: Skirmish
        warrior: Warrior


class WarriorWasKilled(Event):
    @dataclass(kw_only=True)
    class Context:
        skirmish: Skirmish
        warrior: Warrior
        by_warrior: Warrior


class WarriorWasCaptured(Event):
    @dataclass(kw_only=True)
    class Context:
        skirmish: Skirmish
        warrior: Warrior
        capturing_faction: Faction


class WarriorLostMorale(Event):
    @dataclass(kw_only=True)
    class Context:
        skirmish: Skirmish
        warrior: Warrior
        lost_morale: int


class WarriorGainedMorale(Event):
    @dataclass(kw_only=True)
    class Context:
        skirmish: Skirmish
        warrior: Warrior
        gained_morale: int


class WarriorGainedExperience(Event):
    @dataclass(kw_only=True)
    class Context:
        skirmish: Skirmish
        warrior: Warrior
        gained_experience: int
