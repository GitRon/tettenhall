from django.db import models

from apps.skirmish.managers.faction import FactionManager


class Faction(models.Model):
    name = models.CharField("Name", max_length=100)
    locale = models.CharField("Locale", max_length=10)
    stored_items = models.ManyToManyField(
        "Item",
        verbose_name="Stored items",
        blank=True,
    )
    captured_warriors = models.ManyToManyField(
        "Warrior",
        verbose_name="Captured warriors",
        blank=True,
    )

    objects = FactionManager()

    class Meta:
        verbose_name = "Faction"
        verbose_name_plural = "Factions"
        default_related_name = "factions"

    def __str__(self):
        return self.name
