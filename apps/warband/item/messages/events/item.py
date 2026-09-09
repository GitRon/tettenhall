from dataclasses import dataclass

from queuebie.messages import Event

from apps.warband.faction.models.faction import Faction
from apps.warband.item.models.item import Item
from apps.warband.skirmish.models import Warrior


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


@dataclass(kw_only=True)
class ItemWasLost(Event):
    """
    The item is gone, which is why this carries a name and not an item.

    Django clears the primary key of a deleted instance, so an item row is the one thing a past-tense
    event cannot point at - the same reason ItemSold and ItemBought carry their name alongside.
    """

    faction: Faction
    item_name: str
    month: int


@dataclass(kw_only=True)
class OwnershipChanged(Event):
    previous_owner: Warrior
    item: Item
    new_owner: Faction
