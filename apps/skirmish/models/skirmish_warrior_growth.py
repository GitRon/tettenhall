from django.db import models

from apps.skirmish.managers.skirmish_warrior_growth import SkirmishWarriorGrowthManager
from apps.skirmish.models.skirmish import Skirmish
from apps.skirmish.models.warrior import Warrior


class SkirmishWarriorGrowth(models.Model):
    """
    What one warrior took out of one fight, totalled.

    One row per man rather than one per grant, because the grants arrive in pieces - ten for coming
    through it, twenty-five for every man he put down, then a level and the stats behind it - and a
    player asking what the fight did for him wants the sum. The warrior himself carries totals only,
    so nothing else can answer it per fight.
    """

    skirmish = models.ForeignKey(Skirmish, verbose_name="Skirmish", on_delete=models.CASCADE)
    warrior = models.ForeignKey(Warrior, verbose_name="Warrior", on_delete=models.CASCADE)
    # The side he fought this one on, stamped here rather than read off the warrior later: a captive
    # taken in this very fight is recruited into the faction that beat him. Nullable because a
    # warrior's own faction is - a row without one belongs to no side and no report claims it
    faction = models.ForeignKey(
        "faction.Faction", verbose_name="Faction", null=True, blank=True, on_delete=models.CASCADE
    )

    gained_experience = models.PositiveIntegerField("Gained experience", default=0)
    reached_level = models.PositiveSmallIntegerField("Reached level", null=True, blank=True)

    gained_strength = models.PositiveSmallIntegerField("Gained strength", default=0)
    gained_dexterity = models.PositiveSmallIntegerField("Gained dexterity", default=0)
    gained_max_health = models.PositiveSmallIntegerField("Gained maximum health", default=0)
    gained_max_morale = models.PositiveSmallIntegerField("Gained maximum morale", default=0)
    # What he costs now the growth is on him. The wage rise is half of what a level means to the
    # player, and a report that only announced the gain would be selling him the good half
    new_monthly_salary = models.PositiveSmallIntegerField("New monthly salary", null=True, blank=True)

    objects = SkirmishWarriorGrowthManager()

    class Meta:
        verbose_name = "Skirmish warrior growth"
        verbose_name_plural = "Skirmish warrior growths"
        default_related_name = "skirmish_warrior_growths"
        ordering = ("id",)
        constraints = (
            models.UniqueConstraint(fields=("skirmish", "warrior"), name="unique_growth_per_warrior_and_skirmish"),
        )

    def __str__(self) -> str:
        return f"{self.warrior} ({self.skirmish})"
