from dataclasses import dataclass

from queuebie.messages import Event

from apps.savegame.models.savegame import Savegame
from apps.skirmish.models.skirmish import Skirmish


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
    # Evaluated by the command handler: ending the game mid-fight leaves skirmishes with no victor, and
    # deciding them needs a query the consuming event handler is not allowed to make
    open_skirmish_list: list[Skirmish]
    month: int
