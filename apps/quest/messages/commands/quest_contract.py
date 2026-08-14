from dataclasses import dataclass

from queuebie.messages import Command

from apps.quest.models import QuestContract
from apps.skirmish.models import Skirmish


@dataclass(kw_only=True)
class AssignSkirmishToQuestContract(Command):
    quest_contract: QuestContract
    skirmish: Skirmish


@dataclass(kw_only=True)
class RemoveQuestContractAsActiveQuest(Command):
    # No faction: the contract records the faction that signed it, and carrying a second one alongside
    # it let the two disagree - see handle_remove_quest_contract_as_active_quest
    quest_contract: QuestContract
