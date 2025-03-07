from django.db import models

from apps.faction.managers.culture import CultureManager


class Culture(models.Model):
    name = models.CharField("Name", max_length=100)
    locale = models.CharField("Locale", max_length=10)

    objects = CultureManager()

    class Meta:
        verbose_name = "Culture"
        verbose_name_plural = "Cultures"
        default_related_name = "cultures"

    def __str__(self) -> str:
        return self.name
