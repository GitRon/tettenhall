from dataclasses import dataclass

from queuebie.messages import Event

from apps.faction.models.faction import Faction
from apps.month.models import PlayerMonthLog
from apps.savegame.models.savegame import Savegame
from apps.training.models import Training


@dataclass(kw_only=True)
class MonthPrepared(Event):
    faction: Faction
    savegame: Savegame
    training: Training
    current_month: int


@dataclass(kw_only=True)
class PlayerMonthLogCreated(Event):
    player_month_log: PlayerMonthLog


@dataclass(kw_only=True)
class PlayerMonthLogCleared(Event):
    savegame: Savegame
