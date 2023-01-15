from dataclasses import dataclass

from apps.core.event_loop.messages import Event
from apps.skirmish.models.faction import Faction
from apps.skirmish.models.skirmish import Skirmish
from apps.skirmish.models.warrior import Warrior


class WarriorAttackedWithDamage(Event):
    @dataclass
    class Context:
        skirmish: Skirmish
        warrior: Warrior
        damage: int


class WarriorDefendedDamage(Event):
    @dataclass
    class Context:
        skirmish: Skirmish
        warrior: Warrior
        damage: int


class WarriorTookDamage(Event):
    @dataclass
    class Context:
        skirmish: Skirmish
        attacker: Warrior
        attacker_damage: int
        defender: Warrior
        defender_damage: int
        damage: int


class WarriorWasIncapacitated(Event):
    @dataclass
    class Context:
        skirmish: Skirmish
        warrior: Warrior


class WarriorWasKilled(Event):
    @dataclass
    class Context:
        skirmish: Skirmish
        warrior: Warrior


class WarriorWasCaptured(Event):
    @dataclass
    class Context:
        skirmish: Skirmish
        warrior: Warrior
        capturing_faction: Faction
