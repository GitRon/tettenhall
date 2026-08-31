from django.db import models

from apps.town.buildings.hall import Hall
from apps.town.managers.town import TownManager


class Town(models.Model):
    class HallChoices(models.IntegerChoices):
        HALL_NONE = 0, "No hall"
        HALL_SMALL = 1, "Mead Hall"
        HALL_MEDIUM = 2, "Great Hall"
        HALL_LARGE = 3, "High Hall"

    class WeaponsmithChoices(models.IntegerChoices):
        WEAPONSMITH_NONE = 0, "No weaponsmith"
        WEAPONSMITH_SMALL = 1, "Smithy"
        WEAPONSMITH_MEDIUM = 2, "Forge Hall"
        WEAPONSMITH_LARGE = 3, "Master Forge"

    class MarketChoices(models.IntegerChoices):
        MARKET_NONE = 0, "No marketplace"
        MARKET_SMALL = 1, "Marketplace"
        MARKET_MEDIUM = 2, "Trading Post"
        MARKET_LARGE = 3, "High Market"

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
        # Months count from 1, so 0 is "nothing built yet". Defaulting to 1 made the once-per-month
        # guard fire on a brand-new town and left the whole first month unbuildable.
        help_text="Month the last building was commissioned, 0 if none was",
        default=0,
    )

    objects = TownManager()

    class Meta:
        verbose_name = "Town"
        verbose_name_plural = "Towns"
        default_related_name = "towns"

    def __str__(self) -> str:
        return f"{self.faction.name}"

    def get_building_level_display(self, *, building_type: str, level: int) -> str:
        """
        The name a building level goes by, for any level rather than only the one standing.

        Django generates "get_<field>_display()" for the value in the column, while the upgrade page
        also names the level it offers next. Reading the names off the field keeps that page from
        holding a second copy of them that can drift from the column.
        """
        return dict(self._meta.get_field(building_type).choices)[level]

    def get_monthly_income(self) -> int:
        """
        What the town pays out when a month turns.

        The hall is the only building with a recurring payout and it owns the number, so this reads
        it off the level standing rather than holding a copy. One place for it because the month
        bills it and the cost card promises it, and a card naming a different figure than the month
        pays is the kind of thing a player never forgives.
        """
        return Hall.get_building_by_type(building_type=self.hall).REVENUE_PER_ROUND
