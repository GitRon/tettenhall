from django.db import models

from apps.faction.models.faction import Faction
from apps.skirmish.managers.skirmish import SkirmishManager
from apps.skirmish.models.warrior import Warrior


class Skirmish(models.Model):
    name = models.CharField("Name", max_length=100)
    current_round = models.PositiveSmallIntegerField("Current round", default=1)
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
    victorious_faction = models.ForeignKey(
        Faction,
        verbose_name="Victorious faction",
        related_name="victorious_skirmishes",
        on_delete=models.CASCADE,
        null=True,
        blank=True,
    )
    player_warriors = models.ManyToManyField(
        Warrior,
        verbose_name="Player warriors",
        related_name="player_skirmishes",
    )
    non_player_warriors = models.ManyToManyField(
        Warrior,
        verbose_name="Non-player warriors",
        related_name="non_player_skirmishes",
    )

    objects = SkirmishManager()

    class Meta:
        verbose_name = "Skirmish"
        verbose_name_plural = "Skirmishes"
        default_related_name = "skirmishes"

    def __str__(self):
        return self.name
