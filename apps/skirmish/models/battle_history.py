from django.db import models

from apps.skirmish.managers.battle_history import BattleHistoryManager
from apps.skirmish.models.skirmish import Skirmish


class BattleHistory(models.Model):
    message = models.TextField("Message")
    skirmish = models.ForeignKey(Skirmish, verbose_name="Skirmish", on_delete=models.CASCADE)
    created_at = models.DateTimeField("Created at", auto_now_add=True)

    objects = BattleHistoryManager()

    class Meta:
        verbose_name = "Battle log"
        verbose_name_plural = "Battle logs"
        default_related_name = "battle_logs"
        # The one panel in the game that has to read chronologically, so the order it is written in
        # is part of what it is rather than a detail left to the database
        ordering = ("id",)

    def __str__(self) -> str:
        return self.message
