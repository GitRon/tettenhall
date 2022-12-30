from django.db import models

from apps.skirmish.models.faction import Faction


class Skirmish(models.Model):
    name = models.CharField("Name", max_length=100)
    player_faction = models.ForeignKey(
        Faction,
        verbose_name="Player faction",
        related_name="player_skirmishes",
        on_delete=models.CASCADE,
    )
    non_player_faction = models.ForeignKey(
        Faction,
        verbose_name="Non-player faction",
        related_name="non_player_skirmishes",
        on_delete=models.CASCADE,
    )

    class Meta:
        verbose_name = "Skirmish"
        verbose_name_plural = "Skirmishes"
        default_related_name = "skirmishes"

    def __str__(self):
        return self.name
