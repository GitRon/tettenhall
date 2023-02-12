from dataclasses import dataclass

from apps.core.event_loop.messages import Command
from apps.skirmish.models.warrior import Warrior


class ReplenishWarriorMorale(Command):
    @dataclass
    class Context:
        warrior: Warrior
        week: int


class HealInjuredWarrior(Command):
    @dataclass
    class Context:
        warrior: Warrior
        week: int
