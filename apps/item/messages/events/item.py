from dataclasses import dataclass

from apps.core.event_loop.messages import Event
from apps.faction.models.faction import Faction
from apps.item.models.item import Item


class ItemSold(Event):
    @dataclass(kw_only=True)
    class Context:
        selling_faction: Faction
        item: Item
        price: int
