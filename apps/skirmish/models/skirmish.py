from django.db import models

from apps.skirmish.managers.skirmish import SkirmishManager
from apps.skirmish.models.faction import Faction
from apps.skirmish.models.warrior import FightAction, Warrior


class SkirmishWarriorRoundAction(models.Model):
    # todo das kann weg? weil ich die runde nicht persistiere?
    skirmish = models.ForeignKey("Skirmish", verbose_name="Skirmish", on_delete=models.CASCADE)
    warrior = models.ForeignKey(Warrior, verbose_name="Warrior", on_delete=models.CASCADE)
    round = models.PositiveSmallIntegerField("Round")
    action = models.ForeignKey(FightAction, verbose_name="Fight action", on_delete=models.CASCADE)

    class Meta:
        verbose_name = "Skirmish warrior round action"
        verbose_name_plural = "Skirmish warrior round actions"
        default_related_name = "skirmish_warrior_round_actions"

    def __str__(self):
        return f"{self.skirmish}: {self.warrior} ({self.round})"


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
    warrior_round_actions = models.ManyToManyField(
        Warrior,
        through=SkirmishWarriorRoundAction,
        verbose_name="Warrior Round Actions",
        related_name="warrior_round_action_skirmishes",
    )

    objects = SkirmishManager()

    class Meta:
        verbose_name = "Skirmish"
        verbose_name_plural = "Skirmishes"
        default_related_name = "skirmishes"

    def __str__(self):
        return self.name
