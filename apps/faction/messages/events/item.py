from dataclasses import dataclass

from queuebie.messages import Event

from apps.faction.models import Faction
from apps.item.models import Item


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
