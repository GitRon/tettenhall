from dataclasses import dataclass

from apps.core.event_loop.messages import Event
from apps.skirmish.models.skirmish import Skirmish
from apps.skirmish.models.warrior import Warrior


class FighterPairsMatched(Event):
    @dataclass
    class Context:
        skirmish: Skirmish
        warrior_1: Warrior
        warrior_2: Warrior
        attack_action_1: int
        attack_action_2: int


class AttackerDefenderDecided(Event):
    @dataclass
    class Context:
        skirmish: Skirmish
        attacker: Warrior
        defender: Warrior
        attack_action: int


class RoundFinished(Event):
    @dataclass
    class Context:
        skirmish: Skirmish


class SkirmishFinished(Event):
    @dataclass
    class Context:
        skirmish: Skirmish
