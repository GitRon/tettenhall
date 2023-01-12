from dataclasses import dataclass

from apps.core.domain.events import SyncEvent
from apps.skirmish.models.warrior import Warrior

# todo past tense


class WarriorAttacksWithDamage(SyncEvent):
    @dataclass
    class Context:
        warrior: Warrior
        damage: int


class WarriorDefendsDamage(SyncEvent):
    @dataclass
    class Context:
        warrior: Warrior
        damage: int


class WarriorTakesDamage(SyncEvent):
    @dataclass
    class Context:
        attacker: Warrior
        attacker_damage: int
        defender: Warrior
        defender_damage: int
        damage: int


class WarriorIsIncapacitated(SyncEvent):
    @dataclass
    class Context:
        warrior: Warrior
        condition: int
