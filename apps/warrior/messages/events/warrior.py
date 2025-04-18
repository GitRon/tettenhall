from dataclasses import dataclass

from queuebie.messages import Event

from apps.faction.models import Faction
from apps.item.models import Item
from apps.savegame.models.savegame import Savegame
from apps.skirmish.models import Skirmish
from apps.skirmish.models.warrior import Warrior


@dataclass(kw_only=True)
class WarriorMoraleReplenished(Event):
    warrior: Warrior
    faction: Faction
    recovered_morale: int
    month: int


@dataclass(kw_only=True)
class WarriorHealthHealed(Event):
    warrior: Warrior
    faction: Faction
    healed_points: int
    month: int


@dataclass(kw_only=True)
class NewLeaderWarriorCreated(Event):
    warrior: Warrior
    faction: Faction


@dataclass(kw_only=True)
class WarriorCreated(Event):
    warrior: Warrior
    savegame: Savegame
    faction: Faction
    month: int


@dataclass(kw_only=True)
class WarriorItemsDropped(Event):
    skirmish: Skirmish
    warrior: Warrior
    items: list[Item]
