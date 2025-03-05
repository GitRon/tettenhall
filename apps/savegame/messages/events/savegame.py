from dataclasses import dataclass

from queuebie.messages import Event

from apps.savegame.models.savegame import Savegame


@dataclass(kw_only=True)
class NewSavegameCreated(Event):
    savegame: Savegame
    faction_name: str
    town_name: str
    faction_culture_id: int
