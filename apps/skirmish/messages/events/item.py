from dataclasses import dataclass

from apps.core.event_loop.messages import Event
from apps.skirmish.models.faction import Faction
from apps.skirmish.models.item import Item
from apps.skirmish.models.skirmish import Skirmish
from apps.skirmish.models.warrior import Warrior


class ItemDroppedAsLoot(Event):
    @dataclass
    class Context:
        skirmish: Skirmish
        warrior: Warrior
        item: Item
        new_owner: Faction
