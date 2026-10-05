from dataclasses import dataclass, field

from queuebie.messages import Command

from apps.warband.faction.models import Faction
from apps.warband.savegame.models.savegame import Savegame


@dataclass(kw_only=True)
class PrepareMonth(Command):
    savegame: Savegame
    # The month being finished, as the page the player clicked on showed it
    month: int


@dataclass(kw_only=True)
class CreatePlayerMonthLog(Command):
    title: str
    kind: int
    month: int
    faction: Faction
    # Only a chronicle entry has a second sentence to say, so every other producer leaves it alone
    body: str = ""
    # The tags set under a chronicle entry, already worded by the producer
    tags: list[str] = field(default_factory=list)


@dataclass(kw_only=True)
class ClearPlayerMonthLog(Command):
    savegame: Savegame
    current_month: int
