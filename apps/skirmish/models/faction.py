from django.db import models


class Faction(models.Model):
    name = models.CharField("Name", max_length=100)
    locale = models.CharField("Locale", max_length=10)

    class Meta:
        verbose_name = "Faction"
        verbose_name_plural = "Factions"
        default_related_name = "factions"

    def __str__(self):
        return self.name
