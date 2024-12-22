from dataclasses import dataclass

from apps.core.event_loop.messages import Command
from apps.faction.models.faction import Faction
from apps.quest.models.quest import Quest
from apps.skirmish.models.warrior import Warrior


class AcceptQuest(Command):
    @dataclass
    class Context:
        accepting_faction: Faction
        quest: Quest
        assigned_warriors: list[Warrior]
