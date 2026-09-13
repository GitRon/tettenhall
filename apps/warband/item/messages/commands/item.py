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


@dataclass(kw_only=True)
class EquipItem(Command):
    """
    Put a piece of the faction's gear into one warrior's slot, wherever it currently is.

    The item may be lying in the stash or hanging off another warrior, and the handler settles which.
    That second case is why this is a command at all: taking a sword off one man and putting it on
    another is two rows written in one action, and the "OneToOneField" underneath will only accept
    them together.

    "slot" is carried rather than read off the item, because emptying a slot carries no item to read
    it off. It is the name of the field on Warrior - see [Item.gear_slot], which is where a slot name
    comes from when there is an item to ask.
    """

    warrior: Warrior
    item: Item | None
    slot: str
