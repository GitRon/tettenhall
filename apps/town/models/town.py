from django.db import models

from apps.town.managers.town import TownManager


class Town(models.Model):
    class HallChoices(models.IntegerChoices):
        HALL_NONE = 0, "No hall"
        HALL_SMALL = 1, "Mead Hall"
        HALL_MEDIUM = 2, "Great Hall"
        HALL_LARGE = 3, "High Hall"

    # TODO: upgrading works, but the levels grant nothing yet
    class WeaponsmithChoices(models.IntegerChoices):
        WEAPONSMITH_NONE = 0, "No weaponsmith"
        WEAPONSMITH_SMALL = 1, "Smithy"
        WEAPONSMITH_MEDIUM = 2, "Forge Hall"
        WEAPONSMITH_LARGE = 3, "Master Forge"

    # TODO: upgrading works, but the levels grant nothing yet
    class MarketChoices(models.IntegerChoices):
        MARKET_NONE = 0, "No market place"
        MARKET_SMALL = 1, "Market place"
        MARKET_MEDIUM = 2, "Trading post"
        MARKET_LARGE = 3, "High market"

    # TODO: upgrading works, but the levels grant nothing yet
    class SanctuaryChoices(models.IntegerChoices):
        SANCTUARY_NONE = 0, "No sanctuary"
        SANCTUARY_SMALL = 1, "Shrine"
        SANCTUARY_MEDIUM = 2, "Sanctuary"
        SANCTUARY_LARGE = 3, "Great Sanctuary"

    faction = models.OneToOneField("faction.Faction", related_name="town", on_delete=models.CASCADE)
    hall = models.PositiveSmallIntegerField(choices=HallChoices.choices, default=HallChoices.HALL_NONE)
    weaponsmith = models.PositiveSmallIntegerField(
        choices=WeaponsmithChoices.choices, default=WeaponsmithChoices.WEAPONSMITH_NONE
    )
    marketplace = models.PositiveSmallIntegerField(choices=MarketChoices.choices, default=MarketChoices.MARKET_NONE)
    sanctuary = models.PositiveSmallIntegerField(
        choices=SanctuaryChoices.choices, default=SanctuaryChoices.SANCTUARY_NONE
    )
    last_constructed_building_at = models.PositiveSmallIntegerField(
        help_text="Month the last building was commissioned", default=1
    )

    # TODO: training grounds might be interesting as well for faster learning?

    objects = TownManager()

    class Meta:
        verbose_name = "Town"
        verbose_name_plural = "Towns"
        default_related_name = "towns"

    def __str__(self) -> str:
        return f"{self.faction.name}"
