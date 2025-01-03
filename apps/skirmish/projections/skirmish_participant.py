from dataclasses import dataclass

from apps.skirmish.models import Warrior


@dataclass(kw_only=True)
class SkirmishParticipant:
    warrior: Warrior
    skirmish_action: int
