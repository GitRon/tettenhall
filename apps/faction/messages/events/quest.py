from dataclasses import dataclass

from queuebie.messages import Event

from apps.faction.models import Faction
from apps.savegame.models.savegame import Savegame


@dataclass(kw_only=True)
class NewBulletinBoardQuestRequired(Event):
    savegame: Savegame
    faction: Faction
    month: int
