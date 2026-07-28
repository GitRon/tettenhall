from apps.town.buildings.base import Building


class Hall(Building):
    """
    Drives the monthly building income and how many mercenaries the pub holds.

    Revenue grows by less than the costs do, so the largest hall never pays for itself out of income
    alone - what justifies it is the third mercenary slot.
    """

    BUILDING_NAME = "hall"
    BUILDING_LABEL = "Hall"

    REVENUE_PER_ROUND = 0
    AVAILABLE_MERCENARIES = 0

    BUILDING_COSTS = 0

    @classmethod
    def get_levels(cls) -> tuple[type[Building], ...]:
        return (NoHall, SmallHall, MediumHall, LargeHall)


class NoHall(Hall):
    REVENUE_PER_ROUND = 50
    AVAILABLE_MERCENARIES = 1

    BUILDING_COSTS = 0


class SmallHall(Hall):
    REVENUE_PER_ROUND = 300
    AVAILABLE_MERCENARIES = 1

    BUILDING_COSTS = 900


class MediumHall(Hall):
    REVENUE_PER_ROUND = 550
    AVAILABLE_MERCENARIES = 2

    BUILDING_COSTS = 2100


class LargeHall(Hall):
    REVENUE_PER_ROUND = 750
    AVAILABLE_MERCENARIES = 3

    BUILDING_COSTS = 4200
