from django.db import models

from apps.skirmish.managers.skirmish_casualty import SkirmishCasualtyManager
from apps.skirmish.models.skirmish import Skirmish
from apps.skirmish.models.warrior import Warrior


class SkirmishCasualty(models.Model):
    """
    What became of one man in one fight: he fell, he was taken, or his nerve went.

    Recorded as it happens rather than read back off the warrior, because nothing about him survives
    to be read. The monthly sweep clears an unconscious man back to healthy and a routed one back to
    steady, and a capture clears the faction a report is scoped by - so a report assembled in month
    five from the warriors themselves would tell a different story than the one it told on the day.

    One row per man per fight. A man knocked out on the losing side is then taken prisoner, which is
    two events about one casualty, and what the report has to say is the second of them.
    """

    class FateChoices(models.IntegerChoices):
        FATE_FLED = 1, "Fled the field"
        FATE_INCAPACITATED = 2, "Knocked unconscious"
        FATE_KILLED = 3, "Killed"
        FATE_CAPTURED = 4, "Taken prisoner"

    skirmish = models.ForeignKey(Skirmish, verbose_name="Skirmish", on_delete=models.CASCADE)
    warrior = models.ForeignKey(Warrior, verbose_name="Warrior", on_delete=models.CASCADE)
    fate = models.PositiveSmallIntegerField("Fate", choices=FateChoices.choices)

    objects = SkirmishCasualtyManager()

    class Meta:
        verbose_name = "Skirmish casualty"
        verbose_name_plural = "Skirmish casualties"
        default_related_name = "skirmish_casualties"
        # The order the men went down in, so a report reads the way the fight went
        ordering = ("id",)
        constraints = (
            models.UniqueConstraint(fields=("skirmish", "warrior"), name="unique_casualty_per_warrior_and_skirmish"),
        )

    def __str__(self) -> str:
        return f"{self.warrior}: {self.get_fate_display()} ({self.skirmish})"
