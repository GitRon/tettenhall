from dataclasses import dataclass

from queuebie.messages import Event

from apps.faction.models.faction import Faction
from apps.quest.models.quest import Quest
from apps.quest.models.quest_contract import QuestContract


@dataclass(kw_only=True)
class NewQuestCreated(Event):
    quest: Quest
    faction: Faction
    month: int


@dataclass(kw_only=True)
class QuestAccepted(Event):
    accepting_faction: Faction
    quest: Quest
    quest_contract: QuestContract
    month: int
