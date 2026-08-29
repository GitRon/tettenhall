from apps.town.buildings.base import Building, BuildingEffect


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

    @classmethod
    def get_effects(cls) -> tuple[BuildingEffect, ...]:
        # A ceiling on the monthly roll rather than a promise, so the wording has to stay vague
        return (BuildingEffect(label="Healed per month at most", value=f"{cls.MAX_HEALING_POINTS} health points"),)


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


# Where a faction the player did not create starts, and stays: nothing upgrades a rival's town, so this
# is the pace its wounded mend at for the whole savegame. The Shrine puts a beaten rival out of the
# fight for a season rather than most of a year, while an invested player still outheals him. Read off
# get_levels() rather than written as a number, so it keeps naming the Shrine if a level is inserted.
NPC_STARTING_SANCTUARY_LEVEL: int = Sanctuary.get_levels().index(SmallSanctuary)
