from dataclasses import dataclass

from apps.core.event_loop.messages import Command
from apps.faction.models.faction import Faction
from apps.item.models.item import Item


class SellItem(Command):
    @dataclass(kw_only=True)
    class Context:
        selling_faction: Faction
        item: Item


class BuyItem(Command):
    @dataclass(kw_only=True)
    class Context:
        buying_faction: Faction
        price: int
        item: Item
