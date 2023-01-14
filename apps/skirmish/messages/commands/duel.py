from dataclasses import dataclass

from apps.core.event_loop.messages import Command
from apps.skirmish.models.skirmish import Skirmish
from apps.skirmish.models.warrior import Warrior


class StartDuel(Command):
    # todo das gibts noch nicht
    @dataclass
    class Context:
        skirmish: Skirmish
        warrior_1: Warrior
        warrior_2: Warrior


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
