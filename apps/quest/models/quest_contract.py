from django.db import models

from apps.faction.models import Faction
from apps.quest.models.quest import Quest
from apps.skirmish.models.warrior import Warrior


class QuestContract(models.Model):
    faction = models.ForeignKey(Faction, on_delete=models.CASCADE, help_text="Faction who signed up for the quest.")
    quest = models.ForeignKey(Quest, verbose_name="Quest", on_delete=models.CASCADE)
    assigned_warriors = models.ManyToManyField(Warrior, verbose_name="Assigned warriors")
    accepted_in_month = models.PositiveSmallIntegerField("Accepted in month")
    skirmish = models.OneToOneField(
        "skirmish.Skirmish",
        verbose_name="Related Skirmish",
        related_name="quest_contract",
        on_delete=models.SET_NULL,
        null=True,
        blank=True,
    )

    class Meta:
        verbose_name = "Quest contract"
        verbose_name_plural = "Quest contracts"
        default_related_name = "quest_contracts"

    def __str__(self) -> str:
        return f"{self.quest.name}"
