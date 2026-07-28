from apps.town.buildings.base import Building


class Sanctuary(Building):
    """
    Drives how fast injured warriors recover between months.

    The points are the upper bound of the monthly healing roll, not a flat amount, so a level raises
    the ceiling rather than guaranteeing it. Mercenaries carry around 20 maximum health, which is
    what makes the Great Sanctuary able to mend one in a single month.
    """

    BUILDING_NAME = "sanctuary"
    BUILDING_LABEL = "Sanctuary"

    MAX_HEALING_POINTS = 0

    BUILDING_COSTS = 0

    @classmethod
    def get_levels(cls) -> tuple[type[Building], ...]:
        return (NoSanctuary, SmallSanctuary, MediumSanctuary, LargeSanctuary)


class NoSanctuary(Sanctuary):
    MAX_HEALING_POINTS = 4

    BUILDING_COSTS = 0


class SmallSanctuary(Sanctuary):
    MAX_HEALING_POINTS = 8

    BUILDING_COSTS = 750


class MediumSanctuary(Sanctuary):
    MAX_HEALING_POINTS = 14

    BUILDING_COSTS = 1750


class LargeSanctuary(Sanctuary):
    MAX_HEALING_POINTS = 20

    BUILDING_COSTS = 3500
