import abc


class Building(abc.ABC):
    BUILDING_COSTS = 0

    @classmethod
    @abc.abstractmethod
    def get_building_by_type(cls, *, building_type: int) -> "Building":
        pass
