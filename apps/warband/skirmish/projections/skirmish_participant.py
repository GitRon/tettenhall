from dataclasses import dataclass

from apps.warband.skirmish.choices.skirmish_action import SkirmishActionTypeHint
from apps.warband.skirmish.models import Warrior


@dataclass(kw_only=True)
class SkirmishParticipant:
    warrior: Warrior
    skirmish_action: SkirmishActionTypeHint
