from django.db import models

from apps.skirmish.managers.skirmish import SkirmishManager
from apps.skirmish.models.warrior import Warrior


class Skirmish(models.Model):
    name = models.CharField("Name", max_length=100)
    current_round = models.PositiveSmallIntegerField("Current round", default=1)
    # The month the fight belongs to. Nothing recorded it before, and a cap on how often the player
    # may march against the same rival has nowhere else to look: a quest contract knows its month,
    # but an attack carries no contract
    month = models.PositiveSmallIntegerField("Month", default=1)

    # Named for the role each side plays in the fight. Which of them the player holds - if either - is
    # a question for the savegame, so nothing here has to be true of every skirmish ever created
    attacking_faction = models.ForeignKey(
        "faction.Faction",
        verbose_name="Attacking faction",
        related_name="attacking_skirmishes",
        on_delete=models.CASCADE,
    )
    defending_faction = models.ForeignKey(
        "faction.Faction",
        verbose_name="Defending faction",
        related_name="defending_skirmishes",
        on_delete=models.CASCADE,
    )
    victorious_faction = models.ForeignKey(
        "faction.Faction",
        verbose_name="Victorious faction",
        related_name="victorious_skirmishes",
        on_delete=models.CASCADE,
        null=True,
        blank=True,
    )
    attacking_warriors = models.ManyToManyField(
        Warrior,
        verbose_name="Attacking warriors",
        related_name="attacking_skirmishes",
    )
    defending_warriors = models.ManyToManyField(
        Warrior,
        verbose_name="Defending warriors",
        related_name="defending_skirmishes",
    )

    objects = SkirmishManager()

    class Meta:
        verbose_name = "Skirmish"
        verbose_name_plural = "Skirmishes"
        default_related_name = "skirmishes"

    def __str__(self) -> str:
        return self.name

    @property
    def rounds_fought(self) -> int:
        """
        How many rounds have been resolved, as opposed to which round is being fought now.

        "current_round" starts at one and is incremented as each round resolves, so it answers "which
        round is this" - right for the header over a fight in progress, and one too many for a column
        counting what a finished fight cost.
        """
        return self.current_round - 1
