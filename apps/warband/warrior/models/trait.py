from django.db import models

from apps.warband.skirmish.models.warrior import Warrior
from apps.warband.warrior.managers.trait import TraitManager
from apps.warband.warrior.models.trait_type import TraitType


class Trait(models.Model):
    """
    One trait on one man.

    A row rather than a column, for the reason [Injury] is one: the row names the thing, and the
    catalogue it points at stays editable. Unlike an injury, a man carries a kind of trait once - being
    a drunkard twice is not a thing - so the pair is unique.

    Kept for good, and never edited once written, so it goes in through "create_record" - see
    docs/patterns/app-layout.md. No month on it: nothing reads when a man became what he is while a
    trait is hidden, and a column nobody reads is a column somebody builds on speculatively.
    """

    warrior = models.ForeignKey(Warrior, verbose_name="Warrior", on_delete=models.CASCADE)
    type = models.ForeignKey(TraitType, verbose_name="Trait type", on_delete=models.CASCADE)

    objects = TraitManager()

    class Meta:
        verbose_name = "Trait"
        verbose_name_plural = "Traits"
        default_related_name = "traits"
        ordering = ("id",)
        constraints = (models.UniqueConstraint(fields=("warrior", "type"), name="trait_once_per_warrior"),)

    def __str__(self) -> str:
        return f"{self.warrior}: {self.type}"
