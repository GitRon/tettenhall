import abc
from dataclasses import dataclass


@dataclass(frozen=True, kw_only=True)
class BuildingEffect:
    """
    One lever a building level grants, ready to be put in front of the player.

    A label and a value rather than a finished sentence: the numbers are the building's own business,
    while the phrasing and the layout around them are the template's.
    """

    label: str
    value: str


class Building(abc.ABC):
    """
    One building of a town, in the variant matching its current level.

    Buildings come in families: a family class naming the building, plus one variant per level
    listing what that level grants. The town stores only the level, so the family class is what
    turns it back into the variant.
    """

    BUILDING_NAME = ""
    BUILDING_LABEL = ""

    # What the level this variant stands for is bought for, and level 0 is free because it is where
    # every town starts.
    #
    # The curve across a family is deliberately uneven: the first paid level is within reach of the
    # 1000 silver a faction opens with and leaves enough behind to pay a month's wages or hire a man,
    # and the step to the second is the steepest in the game at roughly x3.5, the one after it x2. So
    # the opening purse buys a building and a decision about what to do next, while every level above
    # the first is something to save for across several months. The four families keep their order
    # and their spread at every level - the marketplace cheapest because its resale share is worth
    # little in silver, the hall dearest - so the choice between them is the same choice at every
    # rung.
    BUILDING_COSTS = 0

    @classmethod
    @abc.abstractmethod
    def get_levels(cls) -> tuple[type[Building], ...]:
        """
        The variants of this building, ordered by level.

        A method rather than a class attribute because the variants are defined below their family
        class, so the names only resolve once this is called.
        """
        raise NotImplementedError

    @classmethod
    @abc.abstractmethod
    def get_effects(cls) -> tuple[BuildingEffect, ...]:
        """
        What the level this variant stands for grants, in display order.

        Implemented once on the family class and reading the constants through "cls", so a new level
        describes itself out of the numbers it declares. Every variant of a family answers with the
        same labels in the same order - the upgrade page reads a level and the one above it side by
        side.
        """
        raise NotImplementedError

    @classmethod
    def get_max_level(cls) -> int:
        return len(cls.get_levels()) - 1

    @classmethod
    def get_building_by_type(cls, *, building_type: int) -> Building:
        levels = cls.get_levels()
        if not 0 <= building_type < len(levels):
            raise RuntimeError(f"Unknown {cls.BUILDING_NAME} type: {building_type}")

        return levels[building_type]()
