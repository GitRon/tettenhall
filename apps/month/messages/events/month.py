from dataclasses import dataclass

from queuebie.messages import Event

from apps.faction.models.faction import Faction
from apps.month.models import PlayerMonthLog
from apps.savegame.models.savegame import Savegame
from apps.training.models import Training


@dataclass(kw_only=True)
class FactionMonthPrepared(Event):
    """
    A new month has begun for one faction. Raised once per faction of the savegame, the player's
    included - the player is a faction like any other here.

    This is where anything a faction does monthly belongs. Handlers subscribe to it once and then
    apply to everybody, which is why it carries nothing player-specific: the moment a handler needs
    to know whose month it is, it has picked the wrong event.
    """

    faction: Faction
    current_month: int


@dataclass(kw_only=True)
class PlayerMonthPrepared(Event):
    """
    A new month has begun for the human player specifically.

    Only for the things a rival genuinely has no equivalent of: the shops and the bulletin board he
    browses, and the message log he reads. A faction of the savegame gets a FactionMonthPrepared as
    well, so nothing here needs repeating for the player.

    Not the purse, though. Wages, both incomes and the fyrd all sit on FactionMonthPrepared, where
    each of them refuses the side it is not for in its own command handler - keeping them on one event
    is what fixes the order they happen in, and the wage bill has to be billed before either income
    lands.

    The training regimen sits here too, and does not belong: every faction owns a Training row
    from NewFactionCreated on, so training is a player-only activity by registration only.
    Moving it is #48.

    Moving a handler from here to FactionMonthPrepared is how a player-only activity becomes
    something rivals do too - the field names match so that the move is the whole change.
    """

    faction: Faction
    savegame: Savegame
    # None when the player faction has no training row yet - consumers have to guard
    training: Training | None
    current_month: int


@dataclass(kw_only=True)
class PlayerMonthLogCreated(Event):
    player_month_log: PlayerMonthLog


@dataclass(kw_only=True)
class PlayerMonthLogCleared(Event):
    savegame: Savegame
