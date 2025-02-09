from dataclasses import dataclass

from queuebie.messages import Command

from apps.faction.models.faction import Faction
from apps.training.models.training import Training


@dataclass(kw_only=True)
class TrainWarriors(Command):
    faction: Faction
    training: Training
    week: int
