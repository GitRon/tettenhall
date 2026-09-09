from dataclasses import dataclass

from queuebie.messages import Event

from apps.warband.skirmish.models.warrior import Warrior
from apps.warband.training.models import Training


@dataclass(kw_only=True)
class NewTrainingCreated(Event):
    training: Training


@dataclass(kw_only=True)
class WarriorUpgradedSkill(Event):
    warrior: Warrior
    training_category: int
    changed_attribute: str
    month: int
