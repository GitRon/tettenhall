from apps.town.buildings.base import Building


class Hall(Building):
    BUILDING_NAME = "hall"
    BUILDING_LABEL = "Hall"

    REVENUE_PER_ROUND = 0
    AVAILABLE_MERCENARIES = 0

    BUILDING_COSTS = 0

    @classmethod
    def get_levels(cls) -> tuple[type[Building], ...]:
        return (NoHall, SmallHall, MediumHall, LargeHall)


class NoHall(Hall):
    REVENUE_PER_ROUND = 10
    AVAILABLE_MERCENARIES = 1

    BUILDING_COSTS = 0


class SmallHall(Hall):
    REVENUE_PER_ROUND = 500
    AVAILABLE_MERCENARIES = 1

    BUILDING_COSTS = 1000


class MediumHall(Hall):
    REVENUE_PER_ROUND = 1000
    AVAILABLE_MERCENARIES = 2

    BUILDING_COSTS = 2000


class LargeHall(Hall):
    REVENUE_PER_ROUND = 1500
    AVAILABLE_MERCENARIES = 3

    BUILDING_COSTS = 3000
