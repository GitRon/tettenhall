from dataclasses import dataclass

from apps.core.event_loop.messages import Event
from apps.skirmish.models.skirmish import Skirmish
from apps.skirmish.models.warrior import Warrior


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
