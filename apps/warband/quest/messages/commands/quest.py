from dataclasses import dataclass

from queuebie.messages import Command

from apps.warband.faction.models.faction import Faction
from apps.warband.quest.models.quest import Quest
from apps.warband.skirmish.models.warrior import Warrior


@dataclass(kw_only=True)
class OfferQuests(Command):
    faction: Faction
    month: int


@dataclass(kw_only=True)
class AcceptQuest(Command):
    accepting_faction: Faction
    quest: Quest
    assigned_warriors: list[Warrior]
    month: int
