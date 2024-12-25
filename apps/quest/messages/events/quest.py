from dataclasses import dataclass

from apps.core.event_loop.messages import Event
from apps.faction.models.faction import Faction
from apps.quest.models.quest import Quest
from apps.quest.models.quest_contract import QuestContract


class QuestAccepted(Event):
    @dataclass(kw_only=True)
    class Context:
        accepting_faction: Faction
        quest: Quest
        quest_contract: QuestContract
