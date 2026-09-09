from dataclasses import dataclass

from queuebie.messages import Command

from apps.warband.faction.models.faction import Faction


@dataclass(kw_only=True)
class CreateNewTraining(Command):
    faction: Faction


@dataclass(kw_only=True)
class TrainWarriors(Command):
    faction: Faction
    month: int
