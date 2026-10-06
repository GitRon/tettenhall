from dataclasses import dataclass

from queuebie.messages import Event

from apps.warband.faction.models import Faction
from apps.warband.skirmish.models.warrior import Warrior
from apps.warband.town.models import Town


@dataclass(kw_only=True)
class TownBuildingUpgraded(Event):
    town: Town
    faction: Faction
    building_type: str
    new_level: int
    costs: int
    month: int


@dataclass(kw_only=True)
class FeastThrown(Event):
    """
    The war band feasted. Carries who was fed rather than who was mended: the one reaction that mends
    decides that per man off the columns, and the ledger and the month log both need the whole table.
    """

    town: Town
    faction: Faction
    warrior_list: list[Warrior]
    restored_share: float
    costs: int
    month: int


@dataclass(kw_only=True)
class GeldCalled(Event):
    """
    The village paid. The ledger takes the silver, the fyrd reserve gives up the names, and the month log
    reads both halves of the trade.
    """

    town: Town
    faction: Faction
    silver: int
    fyrd_names: int
    month: int
