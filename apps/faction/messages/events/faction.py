from dataclasses import dataclass

from queuebie.messages import Event

from apps.faction.models.faction import Faction
from apps.item.services.generators.item.base import BaseItemGenerator
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
    faction: Faction
    generator_class: type[BaseItemGenerator]
    item_function: int
    month: int


@dataclass(kw_only=True)
class ItemWasAddedToShop(Event):
    faction: Faction
    month: int
