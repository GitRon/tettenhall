from dataclasses import dataclass

from queuebie.messages import Event

from apps.warband.faction.models.faction import Faction
from apps.warband.quest.models.quest_contract import QuestContract
from apps.warband.quest.quests.base import QuestOutcome
from apps.warband.skirmish.models.warrior import Warrior


@dataclass(kw_only=True)
class QuestContractReturned(Event):
    faction: Faction
    quest_contract: QuestContract
    # The men who came home, resolved by the command handler: a man sent can have left the roster
    # while he was away, and only the ones still on it share in what the quest brought back
    warriors: list[Warrior]
    outcome: QuestOutcome
    month: int


@dataclass(kw_only=True)
class QuestContractLapsed(Event):
    """Every man sent on the quest is gone from the roster, so nobody came home to say how it went."""

    faction: Faction
    quest_contract: QuestContract
    month: int
