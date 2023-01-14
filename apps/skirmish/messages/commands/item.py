from dataclasses import dataclass

from apps.core.event_loop.messages import Command
from apps.skirmish.models.item import Item
from apps.skirmish.models.skirmish import Skirmish
from apps.skirmish.models.warrior import Warrior


class ItemLootDropped(Command):
    @dataclass
    class Context:
        skirmish: Skirmish
        warrior: Warrior
        item: Item
