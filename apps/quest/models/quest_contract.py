from django.db import models

from apps.quest.models.quest import Quest
from apps.skirmish.models.warrior import Warrior


class QuestContract(models.Model):
    # todo: FK missing to "me" so I know who took the quest
    quest = models.ForeignKey(Quest, verbose_name="Quest", on_delete=models.CASCADE)
    assigned_warriors = models.ManyToManyField(Warrior, verbose_name="Assigned warriors")

    class Meta:
        verbose_name = "Quest contract"
        verbose_name_plural = "Quest contracts"
        default_related_name = "quest_contracts"

    def __str__(self) -> str:
        return f"{self.quest.name}"
