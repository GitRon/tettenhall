from dataclasses import dataclass

from apps.core.domain.events import SyncEvent
from apps.skirmish.models.item import Item
from apps.skirmish.models.warrior import Warrior


class ItemLootDropped(SyncEvent):
    @dataclass
    class Context:
        warrior: Warrior
        item: Item
