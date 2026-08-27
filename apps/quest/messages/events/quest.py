from dataclasses import dataclass

from queuebie.messages import Event

from apps.faction.models.faction import Faction
from apps.quest.models.quest import Quest
from apps.quest.models.quest_contract import QuestContract
from apps.skirmish.models.warrior import Warrior


@dataclass(kw_only=True)
class NewQuestCreated(Event):
    quest: Quest
    faction: Faction
    month: int


@dataclass(kw_only=True)
class QuestAccepted(Event):
    accepting_faction: Faction
    target_faction: Faction
    quest: Quest
    quest_contract: QuestContract
    # The men the target turns out, already resolved: picking them reads its roster, and the handler
    # of this event may not - strict mode blocks the database there
    target_warriors: list[Warrior]
    month: int
