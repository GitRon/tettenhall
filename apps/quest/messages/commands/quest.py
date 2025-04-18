from dataclasses import dataclass

from queuebie.messages import Command

from apps.faction.models.faction import Faction
from apps.quest.models.quest import Quest
from apps.savegame.models.savegame import Savegame
from apps.skirmish.models.warrior import Warrior


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
