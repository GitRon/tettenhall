from django.db import models

from apps.skirmish.managers.battle_log import BattleLogManager
from apps.skirmish.models.skirmish import Skirmish


class BattleLog(models.Model):
    message = models.TextField("Message")
    skirmish = models.ForeignKey(
        Skirmish, verbose_name="Skirmish", on_delete=models.CASCADE
    )
    created_at = models.DateTimeField("Created at", auto_now_add=True)

    objects = BattleLogManager()

    class Meta:
        verbose_name = "Battle log"
        verbose_name_plural = "Battle logs"
        default_related_name = "battle_logs"

    def __str__(self):
        return self.message
