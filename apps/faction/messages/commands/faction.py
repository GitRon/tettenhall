from dataclasses import dataclass

from queuebie.messages import Command

from apps.faction.models.faction import Faction
from apps.item.models import Item
from apps.quest.models import Quest
from apps.savegame.models.savegame import Savegame
from apps.skirmish.models import Warrior


@dataclass(kw_only=True)
class CreateNewFaction(Command):
    name: str
    culture_id: int
    savegame: Savegame
    is_player_faction: bool


@dataclass(kw_only=True)
class ReplenishFyrdReserve(Command):
    faction: Faction
    month: int


@dataclass(kw_only=True)
class PayMonthlyWarriorSalaries(Command):
    faction: Faction
    month: int


@dataclass(kw_only=True)
class DetermineWarriorsWithLowMorale(Command):
    faction: Faction
    month: int


@dataclass(kw_only=True)
class DetermineInjuredWarriors(Command):
    faction: Faction
    month: int


@dataclass(kw_only=True)
class SetNewLeaderWarrior(Command):
    warrior: Warrior
    faction: Faction


@dataclass(kw_only=True)
class RestockTownShopItems(Command):
    faction: Faction
    month: int


@dataclass(kw_only=True)
class AddItemToTownShop(Command):
    faction: Faction
    item: Item
    month: int


@dataclass(kw_only=True)
class AddWarriorToPub(Command):
    savegame: Savegame
    faction: Faction
    warrior: Warrior
    month: int


@dataclass(kw_only=True)
class AddQuestToBulletinBoard(Command):
    faction: Faction
    quest: Quest
    month: int


@dataclass(kw_only=True)
class RemoveQuestFromBulletinBoard(Command):
    faction: Faction
    quest: Quest
    month: int
