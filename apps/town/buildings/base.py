import abc


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
    def get_levels(cls) -> tuple[type["Building"], ...]:
        """
        The variants of this building, ordered by level.

        A method rather than a class attribute because the variants are defined below their family
        class, so the names only resolve once this is called.
        """
        raise NotImplementedError

    @classmethod
    def get_max_level(cls) -> int:
        return len(cls.get_levels()) - 1

    @classmethod
    def get_building_by_type(cls, *, building_type: int) -> "Building":
        levels = cls.get_levels()
        if not 0 <= building_type < len(levels):
            raise RuntimeError(f"Unknown {cls.BUILDING_NAME} type: {building_type}")

        return levels[building_type]()
