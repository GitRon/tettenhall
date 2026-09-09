from dataclasses import dataclass

from queuebie.messages import Event

from apps.warband.faction.models.faction import Faction
from apps.warband.item.models.item import Item
from apps.warband.skirmish.models.skirmish import Skirmish
from apps.warband.skirmish.models.warrior import Warrior


@dataclass(kw_only=True)
class ItemDroppedAsLoot(Event):
    skirmish: Skirmish
    warrior: Warrior
    item: Item
    item_name: str
    new_owner: Faction
