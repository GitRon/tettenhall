from dataclasses import dataclass

from queuebie.messages import Event

from apps.warband.faction.models import Faction
from apps.warband.item.models import Item


@dataclass(kw_only=True)
class ItemWasAddedToShop(Event):
    faction: Faction
    item: Item
    month: int


@dataclass(kw_only=True)
class ItemWasRemovedFromShop(Event):
    faction: Faction
    item: Item
    month: int


@dataclass(kw_only=True)
class TownShopRestocked(Event):
    """
    The shop has been emptied and this month's stock requested.

    Raised once for the whole restock, against ItemWasAddedToShop firing per item - a line per item
    would bury the rest of the month.
    """

    faction: Faction
    new_items: int
    month: int
