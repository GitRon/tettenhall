from dataclasses import dataclass

from apps.warband.item.models.item_type import ItemType
from apps.warband.quest.models.quest import Quest
from apps.warband.quest.quests.base import Quest as QuestEntry
from apps.warband.skirmish.models.warrior import Warrior

# The range sign the board writes its "Men" span with
EN_DASH = "\N{EN DASH}"


def _get_range_label(*, amounts: list[int]) -> str | None:
    """
    What the outcomes pay between them, as a range and never as a promise: the outcome is a draw.

    "Up to" where the worst of them pays nothing, so a quest that can come home empty-handed does not
    read as one that always pays a little. None where none of them pays at all.
    """
    least, most = min(amounts), max(amounts)

    if most == 0:
        return None
    if least == most:
        return str(most)
    if least == 0:
        return f"up to {most}"
    return f"{least}{EN_DASH}{most}"


@dataclass(kw_only=True)
class BoardQuest:
    """
    One offer on the board, read together with the catalogue entry that says what it asks for.

    The row stores only which entry it is, so the facts a player decides on - how many men, weighed on
    what, what it can bring home - come off the class, the one place they are written.
    """

    quest: Quest
    entry: type[QuestEntry]

    @property
    def leans_on_label(self) -> str:
        return Warrior._meta.get_field(self.entry.LEANS_ON).verbose_name

    @property
    def leans_on_hint(self) -> str:
        # "Between them" because the attribute is summed over the band: two middling men can be
        # worth one good one
        return f"The more {self.leans_on_label.lower()} the men you send have between them, the likelier it goes well."

    @property
    def silver_per_man_label(self) -> str | None:
        return _get_range_label(amounts=[outcome.silver_per_man for outcome in self.entry.OUTCOMES])

    @property
    def renown_per_man_label(self) -> str | None:
        return _get_range_label(amounts=[outcome.renown_per_man for outcome in self.entry.OUTCOMES])

    @property
    def item_labels(self) -> list[str]:
        # Each function once, in the order the outcomes are written, however many outcomes find one
        functions = dict.fromkeys(
            outcome.item_function for outcome in self.entry.OUTCOMES if outcome.item_function is not None
        )
        return [ItemType.FunctionChoices(function).label for function in functions]

    @property
    def brings_a_man(self) -> bool:
        return any(outcome.warrior_generator_class is not None for outcome in self.entry.OUTCOMES)
