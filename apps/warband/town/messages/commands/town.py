from dataclasses import dataclass

from queuebie.messages import Command

from apps.warband.faction.models import Faction
from apps.warband.town.models import Town


@dataclass(kw_only=True)
class UpgradeTownBuilding(Command):
    town: Town
    faction: Faction
    building_type: str
    new_level: int
    costs: int
    month: int
