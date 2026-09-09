from dataclasses import dataclass

from queuebie.messages import Event

from apps.warband.faction.models import Faction
from apps.warband.quest.models import QuestContract


@dataclass(kw_only=True)
class SkirmishToQuestContractAssigned(Event):
    quest_contract: QuestContract


@dataclass(kw_only=True)
class QuestContractAsActiveQuestRemoved(Event):
    quest_contract: QuestContract
    faction: Faction
