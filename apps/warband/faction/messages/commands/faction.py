from dataclasses import dataclass

from queuebie.messages import Command

from apps.warband.faction.models.faction import Faction
from apps.warband.savegame.models.savegame import Savegame
from apps.warband.skirmish.models import Warrior


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
class ChangeFyrdReserve(Command):
    """
    Move the fyrd reserve by a named amount, up or down.

    Signed rather than one command per direction: the reserve is a lever the catalogue of incidents
    both gives and takes with, and two commands would double the plumbing for no reader's benefit.
    Distinct from [ReplenishFyrdReserve], which is the monthly roll and decides its own amount.
    """

    faction: Faction
    change: int
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
    """
    Stand a warrior in the player's pub, and say whether the next restock may sweep him out again.

    "is_pub_stock" is the whole difference between a mercenary the pub generated, whose row exists
    only until somebody hires him, and a man who left a roster and is waiting to be taken back. The
    restock clears its shelf with a row delete, so it has to be told which of the two it is looking
    at - see "Warrior.is_pub_stock".
    """

    savegame: Savegame
    faction: Faction
    warrior: Warrior
    is_pub_stock: bool
    month: int


@dataclass(kw_only=True)
class DefeatFactionOfLostLeader(Command):
    # Carries nothing but the warrior on purpose: the event handlers raising this cannot look up which
    # faction he led, or whether he led one at all, without a query strict mode forbids them
    warrior: Warrior


@dataclass(kw_only=True)
class OccupyFaction(Command):
    """
    Ride into a rival town nobody healthy is left to hold.

    Carries the target and the occupier only. What the town is worth and who leads it are questions
    for the database, and the handler is where they may be asked.
    """

    faction: Faction
    occupying_faction: Faction
    month: int
