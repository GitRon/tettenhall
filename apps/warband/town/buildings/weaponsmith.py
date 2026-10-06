from apps.warband.item.models.item_type import ItemType
from apps.warband.town.buildings.base import Building, BuildingEffect


class Weaponsmith(Building):
    """
    Drives the quality of the gear the town shop stocks.

    Two halves of the one lever. The bands decide which types the shop can stock at all: a town without a
    forge sells what the fields can make, and the fine band is something the forge unlocks rather than a
    coin flip from month one. The bonus is added to the item generator's modifier roll, which raises the
    item's damage and its price and pushes it up the condition ladder. How *many* items the shop holds is
    the marketplace's business.
    """

    BUILDING_NAME = "weaponsmith"
    BUILDING_LABEL = "Weaponsmith"

    SHOP_ITEM_TIERS: frozenset[int] = frozenset({ItemType.TierChoices.TIER_RUSTIC})
    QUALITY_BONUS = 0

    BUILDING_COSTS = 0

    @classmethod
    def get_levels(cls) -> tuple[type[Building], ...]:
        return (NoWeaponsmith, SmallWeaponsmith, MediumWeaponsmith, LargeWeaponsmith)

    @classmethod
    def get_effects(cls) -> tuple[BuildingEffect, ...]:
        best_tier = ItemType.TierChoices(max(cls.SHOP_ITEM_TIERS))

        return (
            BuildingEffect(label="Best gear in the shop", value=best_tier.label),
            BuildingEffect(label="Quality of the shop's wares", value=f"+{cls.QUALITY_BONUS}"),
        )


class NoWeaponsmith(Weaponsmith):
    SHOP_ITEM_TIERS = frozenset({ItemType.TierChoices.TIER_RUSTIC})
    QUALITY_BONUS = 0

    BUILDING_COSTS = 0


class SmallWeaponsmith(Weaponsmith):
    SHOP_ITEM_TIERS = frozenset({ItemType.TierChoices.TIER_RUSTIC, ItemType.TierChoices.TIER_FINE})
    QUALITY_BONUS = 1

    BUILDING_COSTS = 500


class MediumWeaponsmith(Weaponsmith):
    SHOP_ITEM_TIERS = frozenset({ItemType.TierChoices.TIER_RUSTIC, ItemType.TierChoices.TIER_FINE})
    QUALITY_BONUS = 2

    BUILDING_COSTS = 700


class LargeWeaponsmith(Weaponsmith):
    SHOP_ITEM_TIERS = frozenset({ItemType.TierChoices.TIER_RUSTIC, ItemType.TierChoices.TIER_FINE})
    QUALITY_BONUS = 3

    BUILDING_COSTS = 1400
