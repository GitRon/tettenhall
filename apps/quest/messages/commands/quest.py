from dataclasses import dataclass

from apps.core.event_loop.messages import Command
from apps.quest.models.quest import Quest


class AcceptQuest(Command):
    @dataclass
    class Context:
        quest: Quest
