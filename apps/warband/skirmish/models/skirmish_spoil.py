from django.db import models

from apps.warband.skirmish.managers.skirmish_spoil import SkirmishSpoilManager
from apps.warband.skirmish.models.skirmish import Skirmish


class SkirmishSpoil(models.Model):
    """
    One thing a fight handed to a faction: a piece of gear, a purse, a quest payout.

    Recorded as the spoil lands rather than derived afterwards. Nothing else in the database can
    answer "what did this fight get me": an item knows its owner and not the fight that won it, a
    transaction knows its month and not its skirmish, and the prose battle log is not a thing to
    query. A recorded row also still reads correctly once the sword has been sold on.
    """

    class KindChoices(models.IntegerChoices):
        KIND_ITEM_TAKEN = 1, "Item taken"
        KIND_SILVER_LOOTED = 2, "Silver looted"
        KIND_QUEST_REWARD = 3, "Quest reward"

    skirmish = models.ForeignKey(Skirmish, verbose_name="Skirmish", on_delete=models.CASCADE)
    # The side that gained it, which is not always the victor: the winner's own dead are stripped
    # too, and their gear and purses come back to their own faction
    faction = models.ForeignKey("warband.Faction", verbose_name="Gaining faction", on_delete=models.CASCADE)
    kind = models.PositiveSmallIntegerField("Kind", choices=KindChoices.choices)
    # The item is kept as a relation for as long as it exists: it carries the full dice, which is what
    # says whether it beats what your man is wearing. Items do not last - a restock clears the shelf a
    # sold sword ended up on, and lost gear is deleted outright - so the row lets go of it rather than
    # going with it, and reads its name and dice from the snapshot below from then on
    item = models.ForeignKey("warband.Item", verbose_name="Item", null=True, blank=True, on_delete=models.SET_NULL)
    # Written once, when the spoil is recorded, so the report line survives the item it names
    item_name = models.CharField("Item name", max_length=100, blank=True)
    item_dice = models.CharField("Item dice", max_length=20, blank=True)
    warrior = models.ForeignKey(
        "warband.Warrior", verbose_name="Taken from", null=True, blank=True, on_delete=models.CASCADE
    )
    amount = models.PositiveIntegerField("Amount", default=0)
    # The quest's name, the one thing about a spoil that no relation on this row carries
    description = models.CharField("Description", max_length=100, blank=True)

    objects = SkirmishSpoilManager()

    class Meta:
        verbose_name = "Skirmish spoil"
        verbose_name_plural = "Skirmish spoils"
        default_related_name = "skirmish_spoils"
        # The order the spoils were taken in, so a report reads the way the fight ended rather than
        # in whatever order the database hands the rows back
        ordering = ("id",)

    def __str__(self) -> str:
        return f"{self.get_kind_display()} ({self.skirmish})"
