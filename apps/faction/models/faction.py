from django.db import models

from apps.skirmish.managers.faction import FactionManager


class Faction(models.Model):
    name = models.CharField("Name", max_length=100)
    locale = models.CharField("Locale", max_length=10)
    captured_warriors = models.ManyToManyField(
        "skirmish.Warrior",
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

    def get_all_items(self):
        from apps.item.models.item import Item

        return Item.objects.filter(owner=self)
