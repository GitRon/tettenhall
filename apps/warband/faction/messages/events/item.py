from dataclasses import dataclass

from queuebie.messages import Event

from apps.warband.faction.models import Faction
from apps.warband.item.models import Item
from apps.warband.item.services.generators.item.base import BaseItemGenerator
from apps.warband.skirmish.models import Warrior


@dataclass(kw_only=True)
class RequestNewItemForTownShop(Event):
    faction: Faction
    generator_class: type[BaseItemGenerator]
    item_function: int
    month: int
    quality_bonus: int = 0
    item_tiers: frozenset[int] | None = None


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


@dataclass(kw_only=True)
class ShopItemPurchaseApproved(Event):
    """
    A rival has looked over its own shelf and decided to buy this item.

    The whole decision was made before this was raised, so the handler has nothing left to weigh -
    which is what lets a rival's purchase run through the same BuyItem the player's shop dispatches.
    """

    faction: Faction
    item: Item
    month: int


@dataclass(kw_only=True)
class GearHandoutApproved(Event):
    """
    One item a faction has decided to put in one man's slot.

    One event per equip, in the order they have to run, so each becomes an "EquipItem" and the swap
    stays in the one handler that makes it.
    """

    faction: Faction
    warrior: Warrior
    item: Item
    slot: str
