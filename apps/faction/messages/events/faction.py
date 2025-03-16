from dataclasses import dataclass

from queuebie.messages import Event

from apps.faction.models.faction import Faction
from apps.item.models import Item
from apps.item.services.generators.item.base import BaseItemGenerator
from apps.quest.models import Quest
from apps.skirmish.models.warrior import Warrior


@dataclass(kw_only=True)
class NewFactionCreated(Event):
    faction: Faction


@dataclass(kw_only=True)
class FactionFyrdReserveReplenished(Event):
    faction: Faction
    new_recruitees: int
    month: int


@dataclass(kw_only=True)
class MonthlyWarriorSalariesPaid(Event):
    faction: Faction
    amount: int
    month: int


@dataclass(kw_only=True)
class FactionWarriorsWithLowMoraleDetermined(Event):
    faction: Faction
    warrior_list: list[Warrior]
    month: int


@dataclass(kw_only=True)
class NewLeaderWarriorSet(Event):
    faction: Faction
    warrior: Warrior


@dataclass(kw_only=True)
class RequestNewItemForTownShop(Event):
    # TODO: item.py?
    faction: Faction
    generator_class: type[BaseItemGenerator]
    item_function: int
    month: int


@dataclass(kw_only=True)
class ItemWasAddedToShop(Event):
    # TODO: item.py?
    faction: Faction
    item: Item
    month: int


@dataclass(kw_only=True)
class WarriorWasAddedToPub(Event):
    # TODO: warrior.py?
    faction: Faction
    warrior: Warrior
    month: int


@dataclass(kw_only=True)
class QuestWasAddedToBulletinBoard(Event):
    # TODO: quest.py?
    faction: Faction
    quest: Quest
    month: int


@dataclass(kw_only=True)
class QuestWasRemovedFromBulletinBoard(Event):
    # TODO: quest.py?
    faction: Faction
    quest: Quest
    month: int
