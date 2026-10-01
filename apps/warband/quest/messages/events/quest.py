from dataclasses import dataclass

from queuebie.messages import Event

from apps.warband.faction.models.faction import Faction
from apps.warband.quest.models.quest import Quest
from apps.warband.quest.models.quest_contract import QuestContract
from apps.warband.skirmish.models.warrior import Warrior


@dataclass(kw_only=True)
class QuestsOffered(Event):
    faction: Faction
    quests: list[Quest]
    month: int


@dataclass(kw_only=True)
class QuestAccepted(Event):
    accepting_faction: Faction
    quest_contract: QuestContract
    # The men sent, as the list the command handler signed onto the contract - reading them back
    # through the contract is a query the handler of this event may not run
    assigned_warriors: list[Warrior]
    month: int
