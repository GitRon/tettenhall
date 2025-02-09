from django.db import models

from apps.faction.models import Faction
from apps.month.managers.player_month_log import PlayerMonthLogManager


class PlayerMonthLog(models.Model):
    title = models.CharField("Title", max_length=100)
    month = models.PositiveSmallIntegerField("Month")
    faction = models.ForeignKey(Faction, verbose_name="Faction", on_delete=models.CASCADE)

    objects = PlayerMonthLogManager()

    class Meta:
        verbose_name = "Player month log"
        verbose_name_plural = "Player month logs"
        default_related_name = "player_month_logs"

    def __str__(self) -> str:
        return self.title
