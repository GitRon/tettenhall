from dataclasses import dataclass

from queuebie.messages import Command

from apps.warband.faction.models.faction import Faction
from apps.warband.quest.models.quest import Quest
from apps.warband.savegame.models.savegame import Savegame
from apps.warband.skirmish.models.warrior import Warrior


@dataclass(kw_only=True)
class CreateNewQuest(Command):
    savegame: Savegame
    faction: Faction
    month: int


@dataclass(kw_only=True)
class AcceptQuest(Command):
    accepting_faction: Faction
    quest: Quest
    assigned_warriors: list[Warrior]
    month: int
