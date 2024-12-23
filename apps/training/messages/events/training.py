from dataclasses import dataclass

from apps.core.event_loop.messages import Event
from apps.skirmish.models.warrior import Warrior


class WarriorUpgradedSkill(Event):
    @dataclass(kw_only=True)
    class Context:
        warrior: Warrior
        training_category: int
        changed_attribute: str
        week: int
