from dataclasses import dataclass

from queuebie.messages import Event

from apps.quest.models import QuestContract


@dataclass(kw_only=True)
class SkirmishToQuestContractAssigned(Event):
    quest_contract: QuestContract
