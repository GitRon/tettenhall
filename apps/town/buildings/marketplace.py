from apps.town.buildings.base import Building, BuildingEffect


class Marketplace(Building):
    """
    Drives how much of an item's list price selling it brings in, and how many items the shop holds.

    Buying stays at the full list price, so the ratio is the spread between the two: without a market
    of your own you are fleeced, and selling something back is always a loss.

    Priced below the other buildings because the resale share is worth little in silver at current
    item prices - the stock size is the real draw.

    The share is a whole percentage rather than a float: a float ratio makes the payout depend on
    binary representation error, so 110 silver at 55% and 90 at 85% round to opposite sides of the
    same half and two sales at the same advertised share differ by a silver.
    """

    BUILDING_NAME = "marketplace"
    BUILDING_LABEL = "Marketplace"

    SELL_PERCENTAGE = 0
    AVAILABLE_ITEMS = 0

    BUILDING_COSTS = 0

    @classmethod
    def get_levels(cls) -> tuple[type[Building], ...]:
        return (NoMarketplace, SmallMarketplace, MediumMarketplace, LargeMarketplace)

    @classmethod
    def get_effects(cls) -> tuple[BuildingEffect, ...]:
        return (
            BuildingEffect(label="Paid when selling an item", value=f"{cls.SELL_PERCENTAGE}% of its price"),
            BuildingEffect(label="Items in the shop", value=str(cls.AVAILABLE_ITEMS)),
        )


class NoMarketplace(Marketplace):
    SELL_PERCENTAGE = 40
    AVAILABLE_ITEMS = 3

    BUILDING_COSTS = 0


class SmallMarketplace(Marketplace):
    SELL_PERCENTAGE = 55
    AVAILABLE_ITEMS = 4

    BUILDING_COSTS = 600


class MediumMarketplace(Marketplace):
    SELL_PERCENTAGE = 70
    AVAILABLE_ITEMS = 6

    BUILDING_COSTS = 1400


class LargeMarketplace(Marketplace):
    SELL_PERCENTAGE = 85
    AVAILABLE_ITEMS = 8

    BUILDING_COSTS = 2800
