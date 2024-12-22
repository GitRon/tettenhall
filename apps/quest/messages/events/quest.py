from dataclasses import dataclass

from apps.core.event_loop.messages import Event
from apps.quest.models.quest import Quest
from apps.skirmish.models.warrior import Warrior


class QuestAccepted(Event):
    @dataclass
    class Context:
        quest: Quest
        assigned_warriors: list[Warrior]
