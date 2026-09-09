from dataclasses import dataclass

from queuebie.messages import Event

from apps.warband.faction.models import Faction
from apps.warband.savegame.models.savegame import Savegame


@dataclass(kw_only=True)
class NewBulletinBoardQuestRequired(Event):
    savegame: Savegame
    faction: Faction
    month: int


@dataclass(kw_only=True)
class BulletinBoardQuestsOffered(Event):
    """
    The board has been cleared and this month's quests requested.

    Carries the count rather than the quests: NewBulletinBoardQuestRequired only asks for them, so
    at the moment this is raised none of them exists yet.
    """

    faction: Faction
    new_quests: int
    month: int
