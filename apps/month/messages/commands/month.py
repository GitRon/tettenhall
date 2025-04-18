from dataclasses import dataclass

from queuebie.messages import Command

from apps.faction.models import Faction
from apps.savegame.models.savegame import Savegame


@dataclass(kw_only=True)
class PrepareMonth(Command):
    savegame: Savegame


@dataclass(kw_only=True)
class CreatePlayerMonthLog(Command):
    title: str
    month: int
    faction: Faction


@dataclass(kw_only=True)
class ClearPlayerMonthLog(Command):
    savegame: Savegame
    current_month: int
