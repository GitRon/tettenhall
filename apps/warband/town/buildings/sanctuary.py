from apps.warband.town.buildings.base import Building, BuildingEffect


class Sanctuary(Building):
    """
    Drives how fast injured warriors recover between months, and what it costs to mend one at once.

    The points are the upper bound of the monthly healing roll, not a flat amount, so a level raises
    the ceiling rather than guaranteeing it. Mercenaries carry around 40 maximum health, which is
    what makes the Great Sanctuary able to mend one in a single month.

    The player may also pay the sanctuary to tend one man back to full health now. A treatment mends
    him whole, so the monthly ceiling says nothing about a tended man - the price is where the
    building keeps its say. It is per point mended: a scratch costs little and a man carried off the
    field senseless costs most, which is what makes it silver set against the months he would
    otherwise wait out. A town without a sanctuary cannot tend at all.
    """

    BUILDING_NAME = "sanctuary"
    BUILDING_LABEL = "Sanctuary"

    MAX_HEALING_POINTS = 0
    # Zero is "this sanctuary cannot tend", not "tending for free"
    TENDING_PRICE_PER_POINT = 0

    BUILDING_COSTS = 0

    @classmethod
    def get_levels(cls) -> tuple[type[Building], ...]:
        return (NoSanctuary, SmallSanctuary, MediumSanctuary, LargeSanctuary)

    @classmethod
    def get_effects(cls) -> tuple[BuildingEffect, ...]:
        return (
            # A ceiling on the monthly roll rather than a promise, so the wording has to stay vague
            BuildingEffect(label="Healed per month at most", value=f"{cls.MAX_HEALING_POINTS} health points"),
            BuildingEffect(
                label="Tending a man to full health",
                value=f"{cls.TENDING_PRICE_PER_POINT} silver per health point" if cls.can_tend() else "No tending",
            ),
        )

    @classmethod
    def can_tend(cls) -> bool:
        return cls.TENDING_PRICE_PER_POINT > 0

    @classmethod
    def get_tending_price(cls, *, missing_health: int) -> int:
        return cls.TENDING_PRICE_PER_POINT * missing_health


class NoSanctuary(Sanctuary):
    MAX_HEALING_POINTS = 8
    TENDING_PRICE_PER_POINT = 0

    BUILDING_COSTS = 0


class SmallSanctuary(Sanctuary):
    MAX_HEALING_POINTS = 16
    TENDING_PRICE_PER_POINT = 5

    BUILDING_COSTS = 500


class MediumSanctuary(Sanctuary):
    MAX_HEALING_POINTS = 28
    TENDING_PRICE_PER_POINT = 4

    BUILDING_COSTS = 700


class LargeSanctuary(Sanctuary):
    MAX_HEALING_POINTS = 40
    TENDING_PRICE_PER_POINT = 3

    BUILDING_COSTS = 1400


# Where a faction the player did not create starts, and stays: nothing upgrades a rival's town, so this
# is the pace its wounded mend at for the whole savegame. The Shrine puts a beaten rival out of the
# fight for a season rather than most of a year, while an invested player still outheals him. Read off
# get_levels() rather than written as a number, so it keeps naming the Shrine if a level is inserted.
NPC_STARTING_SANCTUARY_LEVEL: int = Sanctuary.get_levels().index(SmallSanctuary)
