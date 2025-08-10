from apps.town.models import Town


class Hall:
    REVENUE_PER_ROUND = 0
    AVAILABLE_MERCENARIES = 0

    BUILDING_COSTS = 0

    @classmethod
    def get_building_by_type(cls, *, hall_type: int) -> "Hall":
        if hall_type == Town.HallChoices.HALL_NONE:
            return NoHall()
        if hall_type == Town.HallChoices.HALL_SMALL:
            return SmallHall()
        if hall_type == Town.HallChoices.HALL_MEDIUM:
            return MediumHall()
        if hall_type == Town.HallChoices.HALL_LARGE:
            return LargeHall()
        raise RuntimeError(f"Unknown hall type: {hall_type}")


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
