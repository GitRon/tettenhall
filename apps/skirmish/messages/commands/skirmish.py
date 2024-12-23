from dataclasses import dataclass

from apps.core.event_loop.messages import Command
from apps.faction.models.faction import Faction
from apps.skirmish.models.skirmish import Skirmish
from apps.skirmish.models.warrior import Warrior


class StartDuel(Command):
    @dataclass(kw_only=True)
    class Context:
        skirmish: Skirmish
        warrior_list_1: dict[int]
        warrior_list_2: dict[int]


class DetermineAttacker(Command):
    @dataclass(kw_only=True)
    class Context:
        skirmish: Skirmish
        warrior_1: Warrior
        action_1: int
        warrior_2: Warrior
        action_2: int


class WarriorAttacksWarriorWithSimpleAttack(Command):
    @dataclass(kw_only=True)
    class Context:
        skirmish: Skirmish
        attacker: Warrior
        defender: Warrior


class WarriorAttacksWarriorWithRiskyAttack(Command):
    @dataclass(kw_only=True)
    class Context:
        skirmish: Skirmish
        attacker: Warrior
        defender: Warrior


class WinSkirmish(Command):
    @dataclass(kw_only=True)
    class Context:
        skirmish: Skirmish
        victorious_faction: Faction
