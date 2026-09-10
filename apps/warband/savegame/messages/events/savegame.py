from dataclasses import dataclass

from queuebie.messages import Event

from apps.warband.faction.models import Faction
from apps.warband.savegame.models.savegame import Savegame
from apps.warband.skirmish.models.skirmish import Skirmish


@dataclass(kw_only=True)
class NewSavegameCreated(Event):
    savegame: Savegame
    faction_name: str
    town_name: str
    faction_culture_id: int


@dataclass(kw_only=True)
class SavegameEnded(Event):
    savegame: Savegame
    outcome: int
    # Resolved by the command handler for the same reason "open_skirmish_list" is: the log line about
    # the ending is written against the player's faction, and reaching it through the savegame is a
    # lazy query the consuming event handler is not allowed to make
    player_faction: Faction
    # Evaluated by the command handler: ending the game mid-fight leaves skirmishes with no victor, and
    # deciding them needs a query the consuming event handler is not allowed to make
    open_skirmish_list: list[Skirmish]
    month: int
