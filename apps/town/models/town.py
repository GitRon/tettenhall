from django.db import models

from apps.town.managers.town import TownManager


class Town(models.Model):
    class HallChoices(models.IntegerChoices):
        HALL_SMALL = 1, "Mead Hall"
        HALL_MEDIUM = 2, "Great Hall"
        HALL_LARGE = 3, "High Hall"

    class WeaponsmithChoices(models.IntegerChoices):
        WEAPONSMITH_SMALL = 1, "Smithy"
        WEAPONSMITH_MEDIUM = 2, "Forge Hall"
        WEAPONSMITH_LARGE = 3, "Master Forge"

    class MarketChoices(models.IntegerChoices):
        MARKET_SMALL = 1, "Market place"
        MARKET_MEDIUM = 2, "Trading post"
        MARKET_LARGE = 3, "High market"

    class SanctuaryChoices(models.IntegerChoices):
        SANCTUARY_SMALL = 1, "Shrine"
        SANCTUARY_MEDIUM = 2, "Sanctuary"
        SANCTUARY_LARGE = 3, "Great Sanctuary"

    faction = models.OneToOneField("faction.Faction", on_delete=models.CASCADE)
    hall = models.PositiveSmallIntegerField(choices=HallChoices.choices, default=HallChoices.HALL_SMALL)
    weaponsmith = models.PositiveSmallIntegerField(
        choices=WeaponsmithChoices.choices, default=WeaponsmithChoices.WEAPONSMITH_SMALL
    )
    marketplace = models.PositiveSmallIntegerField(choices=MarketChoices.choices, default=MarketChoices.MARKET_SMALL)
    sanctuary = models.PositiveSmallIntegerField(
        choices=SanctuaryChoices.choices, default=SanctuaryChoices.SANCTUARY_SMALL
    )

    objects = TownManager()

    class Meta:
        verbose_name = "Town"
        verbose_name_plural = "Towns"
        default_related_name = "towns"

    def __str__(self) -> str:
        return f"{self.faction.name}"
