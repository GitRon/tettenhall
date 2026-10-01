from django.db import models

from apps.warband.quest.managers.quest import QuestManager


class Quest(models.Model):
    """
    An errand the world has put to a faction this month, and nobody has been sent on yet.

    "quest" names the entry's class in the catalogue (`apps/warband/quest/quests/`), which is where
    what the errand wants and what it can bring home are declared - the row only says that it was
    offered, to whom and when. The title and body are copied off the entry when it is offered, so
    the board reads the same whatever the catalogue says by the time the player looks.

    It lives a month at most: the next month's offer replaces whatever was not taken up, and an
    accepted one leaves the board for the contract that records who went.
    """

    faction = models.ForeignKey("warband.Faction", verbose_name="Offered to", on_delete=models.CASCADE)
    month = models.PositiveSmallIntegerField("Offered in month")
    quest = models.CharField("Quest", max_length=50)
    title = models.CharField("Title", max_length=100)
    body = models.TextField("Body", blank=True, default="")

    objects = QuestManager()

    class Meta:
        verbose_name = "Quest"
        verbose_name_plural = "Quests"
        default_related_name = "quests"
        ordering = ("id",)

    def __str__(self) -> str:
        return self.title
