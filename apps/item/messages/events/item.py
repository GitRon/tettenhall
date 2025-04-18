from dataclasses import dataclass

from queuebie.messages import Event

from apps.faction.models.faction import Faction
from apps.item.models.item import Item


@dataclass(kw_only=True)
class ItemCreated(Event):
    owner: Faction
    faction: Faction
    item: Item
    month: int


@dataclass(kw_only=True)
class ItemSold(Event):
    selling_faction: Faction
    item: Item
    item_name: str
    price: int
    month: int


@dataclass(kw_only=True)
class ItemBought(Event):
    buying_faction: Faction
    item: Item
    item_name: str
    price: int
    month: int
