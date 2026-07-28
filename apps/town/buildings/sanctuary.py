from apps.town.buildings.base import Building


class Sanctuary(Building):
    # TODO: what a sanctuary grants per level is still open, so the variants only carry their costs
    BUILDING_NAME = "sanctuary"
    BUILDING_LABEL = "Sanctuary"

    BUILDING_COSTS = 0

    @classmethod
    def get_levels(cls) -> tuple[type[Building], ...]:
        return (NoSanctuary, SmallSanctuary, MediumSanctuary, LargeSanctuary)


class NoSanctuary(Sanctuary):
    BUILDING_COSTS = 0


class SmallSanctuary(Sanctuary):
    BUILDING_COSTS = 1000


class MediumSanctuary(Sanctuary):
    BUILDING_COSTS = 2000


class LargeSanctuary(Sanctuary):
    BUILDING_COSTS = 3000
