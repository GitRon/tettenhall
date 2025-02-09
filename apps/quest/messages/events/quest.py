from dataclasses import dataclass

from queuebie.messages import Event

from apps.faction.models.faction import Faction
from apps.quest.models.quest import Quest
from apps.quest.models.quest_contract import QuestContract


@dataclass(kw_only=True)
class QuestAccepted(Event):
    accepting_faction: Faction
    quest: Quest
    quest_contract: QuestContract
