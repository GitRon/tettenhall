from django.db import models

from apps.warband.quest.managers.quest_contract import QuestContractManager
from apps.warband.skirmish.models.warrior import Warrior


class QuestContract(models.Model):
    """
    The men a faction sent on an errand, and the month they went in.

    Kept after the errand comes home rather than deleted with it: "accepted_in_month" is what says a
    man was away that month, which the roster rules ask while he is gone and the renown fade and the
    training ask once the month has turned. "resolved_in_month" is set once, by the month turn that
    brings the men home, and is what keeps a contract from coming home twice.

    "quest" is the catalogue entry's class name, copied off the offer with its title, because the offer
    row leaves the board the moment men are sent.
    """

    faction = models.ForeignKey(
        "warband.Faction", on_delete=models.CASCADE, help_text="Faction who sent men on the quest."
    )
    quest = models.CharField("Quest", max_length=50)
    title = models.CharField("Title", max_length=100)
    assigned_warriors = models.ManyToManyField(Warrior, verbose_name="Assigned warriors")
    accepted_in_month = models.PositiveSmallIntegerField("Accepted in month")
    resolved_in_month = models.PositiveSmallIntegerField("Resolved in month", null=True, blank=True)

    objects = QuestContractManager()

    class Meta:
        verbose_name = "Quest contract"
        verbose_name_plural = "Quest contracts"
        default_related_name = "quest_contracts"
        ordering = ("id",)

    def __str__(self) -> str:
        return self.title
