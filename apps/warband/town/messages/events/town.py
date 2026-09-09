from dataclasses import dataclass

from queuebie.messages import Event

from apps.warband.faction.models import Faction
from apps.warband.town.models import Town


@dataclass(kw_only=True)
class TownBuildingUpgraded(Event):
    town: Town
    faction: Faction
    building_type: str
    new_level: int
    costs: int
    month: int
