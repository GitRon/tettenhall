from dataclasses import dataclass

from queuebie.messages import Command

from apps.faction.models import Faction
from apps.item.models import Item


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
