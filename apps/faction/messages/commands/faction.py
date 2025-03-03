from dataclasses import dataclass

from queuebie.messages import Command

from apps.faction.models.faction import Faction
from apps.savegame.models.savegame import Savegame


@dataclass(kw_only=True)
class CreateNewFaction(Command):
    name: str
    culture_id: int
    savegame: Savegame
    is_player_faction: bool


@dataclass(kw_only=True)
class ReplenishFyrdReserve(Command):
    faction: Faction
    month: int


@dataclass(kw_only=True)
class PayMonthlyWarriorSalaries(Command):
    faction: Faction
    month: int


@dataclass(kw_only=True)
class DetermineWarriorsWithLowMorale(Command):
    faction: Faction
    month: int


@dataclass(kw_only=True)
class DetermineInjuredWarriors(Command):
    faction: Faction
    month: int
