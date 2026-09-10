from dataclasses import dataclass

from queuebie.messages import Command

from apps.warband.faction.models import Faction
from apps.warband.item.models import Item


@dataclass(kw_only=True)
class RestockTownShopItems(Command):
    faction: Faction
    month: int


@dataclass(kw_only=True)
class AddItemToTownShop(Command):
    faction: Faction
    item: Item
    month: int


@dataclass(kw_only=True)
class RemoveItemFromTownShop(Command):
    faction: Faction
    item: Item
    month: int
