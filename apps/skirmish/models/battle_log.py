from django.db import models


class BattleLog(models.Model):
    message = models.TextField("Message")
    created_at = models.DateTimeField("Created at", auto_now_add=True)

    class Meta:
        verbose_name = "Battle log"
        verbose_name_plural = "Battle logs"
        default_related_name = "battle_logs"

    def __str__(self):
        return self.message
