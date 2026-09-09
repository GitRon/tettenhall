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
