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
    # None when the player faction has no training row yet - consumers have to guard
    training: Training | None
    current_month: int


@dataclass(kw_only=True)
class RivalFactionMonthPrepared(Event):
    """
    A new month has begun for one rival faction. Raised once per rival, next to the single
    MonthPrepared carrying the player's faction.

    The field names deliberately match MonthPrepared's, because the two events are meant to grow
    together: every handler that reacts to a new month by reading nothing but "faction" and
    "current_month" can be extended to the rivals by stacking a second decorator on it, with no
    other change. Eight of MonthPrepared's ten handlers are in that shape today. The remaining two
    read "training" and "savegame", both of which are player-only concepts, which is why neither
    lives on this event.
    """

    faction: Faction
    current_month: int


@dataclass(kw_only=True)
class PlayerMonthLogCreated(Event):
    player_month_log: PlayerMonthLog


@dataclass(kw_only=True)
class PlayerMonthLogCleared(Event):
    savegame: Savegame
