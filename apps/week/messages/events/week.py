from dataclasses import dataclass

from apps.core.event_loop.messages import Event
from apps.faction.models.faction import Faction
from apps.marketplace.models import Marketplace
from apps.training.models import Training


class WeekPrepared(Event):
    @dataclass(kw_only=True)
    class Context:
        marketplace: Marketplace
        faction: Faction
        training: Training
        current_week: int
