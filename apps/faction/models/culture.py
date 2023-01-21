from django.db import models


class Culture(models.Model):
    name = models.CharField("Name", max_length=100)
    locale = models.CharField("Locale", max_length=10)

    class Meta:
        verbose_name = "Culture"
        verbose_name_plural = "Cultures"
        default_related_name = "cultures"

    def __str__(self):
        return self.name
