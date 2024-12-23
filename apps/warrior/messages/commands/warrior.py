from dataclasses import dataclass

from apps.core.event_loop.messages import Command
from apps.faction.models.faction import Faction
from apps.skirmish.models.warrior import Warrior


class ReplenishWarriorMorale(Command):
    @dataclass(kw_only=True)
    class Context:
        warrior: Warrior
        week: int


class HealInjuredWarrior(Command):
    @dataclass(kw_only=True)
    class Context:
        warrior: Warrior
        week: int


class RecruitCapturedWarrior(Command):
    @dataclass(kw_only=True)
    class Context:
        warrior: Warrior
        faction: Faction


class EnslaveCapturedWarrior(Command):
    @dataclass(kw_only=True)
    class Context:
        warrior: Warrior
        faction: Faction
