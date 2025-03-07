from dataclasses import dataclass

from queuebie.messages import Command

from apps.faction.models.faction import Faction
from apps.item.models.item import Item
from apps.item.services.generators.item.base import BaseItemGenerator
from apps.savegame.models.savegame import Savegame


@dataclass(kw_only=True)
class CreateItem(Command):
    owner: Faction | None
    faction: Faction
    generator_class: type[BaseItemGenerator]
    item_function: int
    savegame: Savegame
    month: int


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
