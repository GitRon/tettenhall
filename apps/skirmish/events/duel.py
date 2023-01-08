from dataclasses import dataclass

from apps.core.domain.events import SyncEvent
from apps.skirmish.models.warrior import Warrior


class DuelAttackerDefenderDecided(SyncEvent):
    @dataclass
    class Context:
        attacker: Warrior
        defender: Warrior
