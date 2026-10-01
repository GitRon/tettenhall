from dataclasses import dataclass

from apps.warband.quest.models.quest import Quest
from apps.warband.quest.quests.base import Quest as QuestEntry
from apps.warband.skirmish.models.warrior import Warrior


@dataclass(kw_only=True)
class BoardQuest:
    """
    One offer on the board, read together with the catalogue entry that says what it asks for.

    The row stores only which entry it is, so the facts a player decides on - how many men, weighed on
    what - come off the class, the one place they are written.
    """

    quest: Quest
    entry: type[QuestEntry]

    @property
    def leans_on_label(self) -> str:
        return Warrior._meta.get_field(self.entry.LEANS_ON).verbose_name
