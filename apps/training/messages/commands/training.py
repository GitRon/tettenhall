from dataclasses import dataclass

from apps.core.event_loop.messages import Command
from apps.faction.models.faction import Faction
from apps.training.models.training import Training


class TrainWarriors(Command):
    @dataclass
    class Context:
        faction: Faction
        training: Training
        week: int
