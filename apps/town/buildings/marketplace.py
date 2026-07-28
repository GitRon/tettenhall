from apps.town.buildings.base import Building


class Marketplace(Building):
    """
    Drives how much of an item's list price selling it brings in, and how many items the shop holds.

    Buying stays at the full list price, so the ratio is the spread between the two: without a market
    of your own you are fleeced, and selling something back is always a loss.

    Priced below the other buildings because the resale ratio is worth little in silver at current
    item prices - the stock size is the real draw.
    """

    BUILDING_NAME = "marketplace"
    BUILDING_LABEL = "Marketplace"

    SELL_RATIO = 0.0
    AVAILABLE_ITEMS = 0

    BUILDING_COSTS = 0

    @classmethod
    def get_levels(cls) -> tuple[type[Building], ...]:
        return (NoMarketplace, SmallMarketplace, MediumMarketplace, LargeMarketplace)


class NoMarketplace(Marketplace):
    SELL_RATIO = 0.4
    AVAILABLE_ITEMS = 3

    BUILDING_COSTS = 0


class SmallMarketplace(Marketplace):
    SELL_RATIO = 0.55
    AVAILABLE_ITEMS = 4

    BUILDING_COSTS = 600


class MediumMarketplace(Marketplace):
    SELL_RATIO = 0.7
    AVAILABLE_ITEMS = 6

    BUILDING_COSTS = 1400


class LargeMarketplace(Marketplace):
    SELL_RATIO = 0.85
    AVAILABLE_ITEMS = 8

    BUILDING_COSTS = 2800
