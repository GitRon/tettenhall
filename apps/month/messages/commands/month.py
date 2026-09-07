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
    kind: int
    month: int
    faction: Faction
    # Only a chronicle entry has a second sentence to say, so every other producer leaves it alone
    body: str = ""


@dataclass(kw_only=True)
class ClearPlayerMonthLog(Command):
    savegame: Savegame
    current_month: int
