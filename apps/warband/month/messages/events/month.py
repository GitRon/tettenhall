from dataclasses import dataclass

from queuebie.messages import Event

from apps.warband.faction.models.faction import Faction
from apps.warband.month.models import PlayerMonthLog
from apps.warband.savegame.models.savegame import Savegame


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

    Only for the things a rival genuinely has no equivalent of: the town economy that pays him, the
    shops and the bulletin board he browses, and the message log he reads. A faction of the savegame
    gets a FactionMonthPrepared as well, so nothing here needs repeating for the player.

    Being registered here is a guard in itself, and the cheaper one - the town income needs no check
    of its own because a rival never reaches it. What cannot be settled this way goes on
    FactionMonthPrepared and guards itself in its command handler, the way the rival income refuses
    the player.

    Moving a handler from here to FactionMonthPrepared is how a player-only activity becomes
    something rivals do too - the field names match so that the move is the whole change.
    """

    faction: Faction
    savegame: Savegame
    current_month: int


@dataclass(kw_only=True)
class PlayerMonthLogCreated(Event):
    player_month_log: PlayerMonthLog


@dataclass(kw_only=True)
class PlayerMonthLogCleared(Event):
    savegame: Savegame
