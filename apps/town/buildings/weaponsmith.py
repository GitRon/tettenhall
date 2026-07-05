from apps.town.buildings.base import Building
from apps.town.models import Town


class Weaponsmith(Building):
    AVAILABLE_ITEMS = 0

    BUILDING_COSTS = 0

    @classmethod
    def get_building_by_type(cls, *, building_type: int) -> "Weaponsmith":
        if building_type == Town.WeaponsmithChoices.WEAPONSMITH_NONE:
            return NoWeaponsmith()
        if building_type == Town.WeaponsmithChoices.WEAPONSMITH_SMALL:
            return SmallWeaponsmith()
        if building_type == Town.WeaponsmithChoices.WEAPONSMITH_MEDIUM:
            return MediumWeaponsmith()
        if building_type == Town.WeaponsmithChoices.WEAPONSMITH_LARGE:
            return LargeWeaponsmith()
        raise RuntimeError(f"Unknown weaponsmith type: {building_type}")


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
