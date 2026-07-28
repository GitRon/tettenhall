from apps.town.buildings.base import Building, BuildingEffect


class Weaponsmith(Building):
    """
    Drives the quality of the gear the town shop stocks.

    The bonus is added to the item generator's modifier roll, which raises the item's damage and its
    price and pushes it up the condition ladder. How *many* items the shop holds is the
    marketplace's business.
    """

    BUILDING_NAME = "weaponsmith"
    BUILDING_LABEL = "Weaponsmith"

    QUALITY_BONUS = 0

    BUILDING_COSTS = 0

    @classmethod
    def get_levels(cls) -> tuple[type[Building], ...]:
        return (NoWeaponsmith, SmallWeaponsmith, MediumWeaponsmith, LargeWeaponsmith)

    @classmethod
    def get_effects(cls) -> tuple[BuildingEffect, ...]:
        return (BuildingEffect(label="Quality of the shop's wares", value=f"+{cls.QUALITY_BONUS}"),)


class NoWeaponsmith(Weaponsmith):
    QUALITY_BONUS = 0

    BUILDING_COSTS = 0


class SmallWeaponsmith(Weaponsmith):
    QUALITY_BONUS = 1

    BUILDING_COSTS = 750


class MediumWeaponsmith(Weaponsmith):
    QUALITY_BONUS = 2

    BUILDING_COSTS = 1750


class LargeWeaponsmith(Weaponsmith):
    QUALITY_BONUS = 3

    BUILDING_COSTS = 3500
