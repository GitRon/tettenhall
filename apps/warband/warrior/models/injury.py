from django.db import models

from apps.warband.skirmish.models.warrior import Warrior
from apps.warband.warrior.managers.injury import InjuryManager
from apps.warband.warrior.models.injury_type import InjuryType


class Injury(models.Model):
    """
    One lasting mark on one man, and what it is called.

    A row rather than a column, because a row names the thing - "Stiff ankle", "Missing finger" -
    which is the whole point of the feature, and because a man can carry two of a kind. A bare
    modifier column would be cheaper and unnameable; a flag set caps itself but cannot say *two
    fingers*.

    Kept for good. The sanctuary already has its lever - how fast a man gets back on his feet - and a
    second one that erased the injury would take back the only lasting cost a fight has. Note the
    word: "HealInjuredWarrior" and the monthly sweep mean *wounded*, which is health below the
    maximum and mends every month. This is the other thing, and nothing mends it.

    Never edited once written, so it goes in through "create_record" - see
    docs/patterns/app-layout.md.
    """

    warrior = models.ForeignKey(Warrior, verbose_name="Warrior", on_delete=models.CASCADE)
    type = models.ForeignKey(InjuryType, verbose_name="Injury type", on_delete=models.CASCADE)
    # The month he took it, so a card can say when without the fight having to survive to be asked.
    # A skirmish carries over into the next month, and a savegame's fights are deleted with it.
    inflicted_in_month = models.PositiveSmallIntegerField("Inflicted in month")

    objects = InjuryManager()

    class Meta:
        verbose_name = "Injury"
        verbose_name_plural = "Injuries"
        default_related_name = "injuries"
        # The order he took them in, so a card reads as the history it is
        ordering = ("id",)

    def __str__(self) -> str:
        return f"{self.warrior}: {self.type}"
