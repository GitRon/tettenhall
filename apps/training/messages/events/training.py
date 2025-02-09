from dataclasses import dataclass

from queuebie.messages import Event

from apps.skirmish.models.warrior import Warrior


@dataclass(kw_only=True)
class WarriorUpgradedSkill(Event):
    warrior: Warrior
    training_category: int
    changed_attribute: str
    month: int
