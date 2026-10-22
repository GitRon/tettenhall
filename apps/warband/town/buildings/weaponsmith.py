from apps.warband.item.models.item import Item
from apps.warband.item.models.item_type import ItemType
from apps.warband.town.buildings.base import Building, BuildingEffect


class Weaponsmith(Building):
    """
    Drives the quality of the gear the town shop stocks, and of the gear the war band already owns.

    Three parts of the one lever. The bands decide which types the shop can stock at all: a town without
    a forge sells what the fields can make, and the fine band is something the forge unlocks rather than
    a coin flip from month one. The bonus is added to the item generator's modifier roll, which raises the
    item's damage and its price and pushes it up the condition ladder. The cap is how far up that ladder
    the smith reworks a piece the war band already owns, which is what keeps a better forge paying off for
    the sword a man has carried through ten fights. How *many* items the shop holds is the marketplace's
    business.
    """

    BUILDING_NAME = "weaponsmith"
    BUILDING_LABEL = "Weaponsmith"

    SHOP_ITEM_TIERS: frozenset[int] = frozenset({ItemType.TierChoices.TIER_RUSTIC})
    QUALITY_BONUS = 0
    # The best condition the smith reworks an owned item up to, None where he reworks nothing
    MAX_UPGRADE_CONDITION: int | None = None

    BUILDING_COSTS = 0

    @classmethod
    def get_levels(cls) -> tuple[type[Building], ...]:
        return (NoWeaponsmith, SmallWeaponsmith, MediumWeaponsmith, LargeWeaponsmith)

    @classmethod
    def can_upgrade_item(cls) -> bool:
        return cls.MAX_UPGRADE_CONDITION is not None

    @classmethod
    def get_effects(cls) -> tuple[BuildingEffect, ...]:
        best_tier = ItemType.TierChoices(max(cls.SHOP_ITEM_TIERS))
        upgrade_cap = Item.ConditionChoices(cls.MAX_UPGRADE_CONDITION).label if cls.can_upgrade_item() else "Nothing"

        return (
            BuildingEffect(label="Best gear in the shop", value=best_tier.label),
            BuildingEffect(label="Quality of the shop's wares", value=f"+{cls.QUALITY_BONUS}"),
            BuildingEffect(label="Best a smith makes of old gear", value=upgrade_cap),
        )


class NoWeaponsmith(Weaponsmith):
    SHOP_ITEM_TIERS = frozenset({ItemType.TierChoices.TIER_RUSTIC})
    QUALITY_BONUS = 0
    MAX_UPGRADE_CONDITION = None

    BUILDING_COSTS = 0


class SmallWeaponsmith(Weaponsmith):
    SHOP_ITEM_TIERS = frozenset({ItemType.TierChoices.TIER_RUSTIC, ItemType.TierChoices.TIER_FINE})
    QUALITY_BONUS = 1
    MAX_UPGRADE_CONDITION = Item.ConditionChoices.CONDITION_CHEAP

    BUILDING_COSTS = 500


class MediumWeaponsmith(Weaponsmith):
    SHOP_ITEM_TIERS = frozenset({ItemType.TierChoices.TIER_RUSTIC, ItemType.TierChoices.TIER_FINE})
    QUALITY_BONUS = 2
    MAX_UPGRADE_CONDITION = Item.ConditionChoices.CONDITION_TRADITIONAL

    BUILDING_COSTS = 700


class LargeWeaponsmith(Weaponsmith):
    SHOP_ITEM_TIERS = frozenset({ItemType.TierChoices.TIER_RUSTIC, ItemType.TierChoices.TIER_FINE})
    QUALITY_BONUS = 3
    MAX_UPGRADE_CONDITION = Item.ConditionChoices.CONDITION_SUPERIOR

    BUILDING_COSTS = 1400
