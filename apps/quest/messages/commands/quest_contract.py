from dataclasses import dataclass

from queuebie.messages import Command

from apps.quest.models import QuestContract
from apps.skirmish.models import Skirmish


@dataclass(kw_only=True)
class AssignSkirmishToQuestContract(Command):
    quest_contract: QuestContract
    skirmish: Skirmish
