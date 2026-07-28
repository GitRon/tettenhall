from apps.town.buildings.base import Building


class Weaponsmith(Building):
    BUILDING_NAME = "weaponsmith"
    BUILDING_LABEL = "Weaponsmith"

    AVAILABLE_ITEMS = 0

    BUILDING_COSTS = 0

    @classmethod
    def get_levels(cls) -> tuple[type[Building], ...]:
        return (NoWeaponsmith, SmallWeaponsmith, MediumWeaponsmith, LargeWeaponsmith)


class NoWeaponsmith(Weaponsmith):
    AVAILABLE_ITEMS = 1

    BUILDING_COSTS = 0


class SmallWeaponsmith(Weaponsmith):
    AVAILABLE_ITEMS = 2

    BUILDING_COSTS = 1000


class MediumWeaponsmith(Weaponsmith):
    AVAILABLE_ITEMS = 3

    BUILDING_COSTS = 2000


class LargeWeaponsmith(Weaponsmith):
    AVAILABLE_ITEMS = 4

    BUILDING_COSTS = 3000
