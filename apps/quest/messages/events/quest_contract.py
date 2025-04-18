from dataclasses import dataclass

from queuebie.messages import Event

from apps.faction.models import Faction
from apps.quest.models import QuestContract


@dataclass(kw_only=True)
class SkirmishToQuestContractAssigned(Event):
    quest_contract: QuestContract


@dataclass(kw_only=True)
class QuestContractAsActiveQuestRemoved(Event):
    quest_contract: QuestContract
    faction: Faction
