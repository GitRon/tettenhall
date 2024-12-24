from django.db import models

from apps.week.managers.player_week_log import PlayerWeekLogManager


class PlayerWeekLog(models.Model):
    title = models.CharField("Title", max_length=100)
    message = models.TextField("Message")
    week = models.PositiveSmallIntegerField("Week")

    objects = PlayerWeekLogManager()

    class Meta:
        verbose_name = "Player week log"
        verbose_name_plural = "Player week logs"
        default_related_name = "player_week_logs"

    def __str__(self) -> str:
        return self.message
