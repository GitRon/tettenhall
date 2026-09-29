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


@dataclass(kw_only=True)
class HandOutFactionGear(Command):
    """
    Put this faction's best gear on its best men.

    Raised whenever the gear or the men a faction has to hand it to have changed, rather than at a
    fixed point in the month, so a rival arms the man it has just recruited and the spoils it has just
    won without anybody deciding what comes first. The player is refused - his men are armed by hand.
    """

    faction: Faction
