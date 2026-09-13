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


@dataclass(kw_only=True)
class ItemEquipped(Event):
    """
    A slot was filled, emptied, or filled out of somebody else's hands.

    Both ends of the move ride along, because they are what separate the shapes this one event
    covers and no consumer could tell them apart afterwards: the gear has already moved by the time
    anybody reads this. "previous_holder" is the man the item came off, None when it was lying in
    the stash; "displaced_item" is what came out of the receiving slot, None when it was empty. Both
    set is a swap, and the displaced item went to the previous holder.
    """

    warrior: Warrior
    item: Item | None
    slot: str
    previous_holder: Warrior | None
    displaced_item: Item | None
