from dataclasses import dataclass

from queuebie.messages import Event

from apps.faction.models import Faction
from apps.savegame.models.savegame import Savegame
from apps.skirmish.models.warrior import Warrior


@dataclass(kw_only=True)
class WarriorMoraleReplenished(Event):
    warrior: Warrior
    faction: Faction
    recovered_morale: int
    month: int


@dataclass(kw_only=True)
class WarriorLostMoraleOverUnpaidSalary(Event):
    warrior: Warrior
    faction: Faction
    lost_morale: int
    month: int


@dataclass(kw_only=True)
class WarriorDesertedOverUnpaidSalary(Event):
    warrior: Warrior
    # The faction he walked out on - his own FK is cleared by then
    faction: Faction
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
