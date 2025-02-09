from dataclasses import dataclass

from queuebie.messages import Command

from apps.faction.models.faction import Faction
from apps.quest.models.quest import Quest
from apps.skirmish.models.warrior import Warrior


@dataclass(kw_only=True)
class AcceptQuest(Command):
    accepting_faction: Faction
    quest: Quest
    assigned_warriors: list[Warrior]
    month: int
