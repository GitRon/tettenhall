from dataclasses import dataclass

from apps.core.event_loop.messages import Command
from apps.skirmish.models.skirmish import Skirmish
from apps.skirmish.models.warrior import Warrior


class StartDuel(Command):
    @dataclass
    class Context:
        skirmish: Skirmish
        warrior_list_1: list[Warrior]
        warrior_list_2: list[Warrior]


class DetermineAttacker(Command):
    @dataclass
    class Context:
        skirmish: Skirmish
        warrior_1: Warrior
        action_1: int
        warrior_2: Warrior
        action_2: int


class WarriorAttacksWarriorWithSimpleAttack(Command):
    @dataclass
    class Context:
        skirmish: Skirmish
        attacker: Warrior
        defender: Warrior
