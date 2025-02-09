from dataclasses import dataclass

from queuebie.messages import Event

from apps.faction.models.faction import Faction
from apps.item.models.item import Item
from apps.skirmish.models.skirmish import Skirmish
from apps.skirmish.models.warrior import Warrior


@dataclass(kw_only=True)
class ItemDroppedAsLoot(Event):
    skirmish: Skirmish
    warrior: Warrior
    item: Item
    new_owner: Faction
