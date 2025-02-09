from dataclasses import dataclass

from queuebie.messages import Event

from apps.faction.models.faction import Faction
from apps.marketplace.models import Marketplace
from apps.training.models import Training


@dataclass(kw_only=True)
class WeekPrepared(Event):
    marketplace: Marketplace
    faction: Faction
    training: Training
    current_week: int
