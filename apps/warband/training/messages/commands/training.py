from dataclasses import dataclass

from queuebie.messages import Command

from apps.warband.faction.models.faction import Faction
from apps.warband.training.models import Training


@dataclass(kw_only=True)
class CreateNewTraining(Command):
    faction: Faction


@dataclass(kw_only=True)
class TrainWarriors(Command):
    faction: Faction
    month: int


@dataclass(kw_only=True)
class ChangeTrainingRegimen(Command):
    training: Training
    category: int
