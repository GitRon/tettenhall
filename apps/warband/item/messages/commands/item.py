from dataclasses import dataclass

from queuebie.messages import Command

from apps.warband.faction.models.faction import Faction
from apps.warband.item.models.item import Item
from apps.warband.item.services.generators.item.base import BaseItemGenerator
from apps.warband.skirmish.models import Warrior


@dataclass(kw_only=True)
class CreateItem(Command):
    owner: Faction | None
    faction: Faction
    generator_class: type[BaseItemGenerator]
    item_function: int
    month: int
    quality_bonus: int = 0


@dataclass(kw_only=True)
class SellItem(Command):
    selling_faction: Faction
    item: Item
    month: int


@dataclass(kw_only=True)
class BuyItem(Command):
    buying_faction: Faction
    price: int
    item: Item
    month: int


@dataclass(kw_only=True)
class LoseItem(Command):
    """
    A piece of gear is gone from the game, not sold and not handed on.

    The faction rides along because the item's own owner is about to stop existing, and whoever
    reacts to the loss still has to know whose it was.
    """

    faction: Faction
    item: Item
    month: int


@dataclass(kw_only=True)
class ChangeOwnership(Command):
    previous_owner: Warrior
    item: Item
    new_owner: Faction
