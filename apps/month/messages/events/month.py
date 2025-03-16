from dataclasses import dataclass

from queuebie.messages import Event

from apps.faction.models.faction import Faction
from apps.training.models import Training


@dataclass(kw_only=True)
class MonthPrepared(Event):
    faction: Faction
    training: Training
    current_month: int
