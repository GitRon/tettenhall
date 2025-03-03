from dataclasses import dataclass

from queuebie.messages import Event

from apps.skirmish.models.warrior import Warrior
from apps.training.models import Training


@dataclass(kw_only=True)
class NewTrainingCreated(Event):
    training: Training


@dataclass(kw_only=True)
class WarriorUpgradedSkill(Event):
    warrior: Warrior
    training_category: int
    changed_attribute: str
    month: int
