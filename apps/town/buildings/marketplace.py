from apps.town.buildings.base import Building


class Marketplace(Building):
    # TODO: what a market grants per level is still open, so the variants only carry their costs
    BUILDING_NAME = "marketplace"
    BUILDING_LABEL = "Marketplace"

    BUILDING_COSTS = 0

    @classmethod
    def get_levels(cls) -> tuple[type[Building], ...]:
        return (NoMarketplace, SmallMarketplace, MediumMarketplace, LargeMarketplace)


class NoMarketplace(Marketplace):
    BUILDING_COSTS = 0


class SmallMarketplace(Marketplace):
    BUILDING_COSTS = 1000


class MediumMarketplace(Marketplace):
    BUILDING_COSTS = 2000


class LargeMarketplace(Marketplace):
    BUILDING_COSTS = 3000
