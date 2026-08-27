from dataclasses import dataclass

from queuebie.messages import Command

from apps.faction.models.faction import Faction
from apps.quest.models import Quest
from apps.savegame.models.savegame import Savegame
from apps.skirmish.models import Warrior


@dataclass(kw_only=True)
class CreateNewFaction(Command):
    name: str
    town_name: str
    culture_id: int
    savegame: Savegame
    is_player_faction: bool


@dataclass(kw_only=True)
class CreateFactionsForNewSavegame(Command):
    savegame: Savegame
    faction_name: str
    town_name: str
    faction_culture_id: int


@dataclass(kw_only=True)
class ReplenishFyrdReserve(Command):
    faction: Faction
    month: int


@dataclass(kw_only=True)
class PayMonthlyWarriorSalaries(Command):
    faction: Faction
    month: int


@dataclass(kw_only=True)
class EarnMoneyFromBuildings(Command):
    faction: Faction
    month: int


@dataclass(kw_only=True)
class EarnMonthlyFactionIncome(Command):
    faction: Faction
    month: int


@dataclass(kw_only=True)
class DetermineWarriorsWithReducedMorale(Command):
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
class AddWarriorToPub(Command):
    savegame: Savegame
    faction: Faction
    warrior: Warrior
    month: int


@dataclass(kw_only=True)
class RemoveQuestFromBulletinBoard(Command):
    faction: Faction
    quest: Quest
    month: int


@dataclass(kw_only=True)
class DefeatFactionOfLostLeader(Command):
    # Carries nothing but the warrior on purpose: the event handlers raising this cannot look up which
    # faction he led, or whether he led one at all, without a query strict mode forbids them
    warrior: Warrior
