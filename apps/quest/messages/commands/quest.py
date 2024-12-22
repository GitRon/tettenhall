from dataclasses import dataclass

from apps.core.event_loop.messages import Command
from apps.quest.models.quest import Quest
from apps.skirmish.models.warrior import Warrior


class AcceptQuest(Command):
    @dataclass
    class Context:
        quest: Quest
        assigned_warriors: list[Warrior]
