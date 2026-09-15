from dataclasses import dataclass

from queuebie.messages import Command

from apps.warband.faction.models.faction import Faction
from apps.warband.savegame.models.savegame import Savegame
from apps.warband.skirmish.models import Warrior


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
class EarnMoneyFromBuildings(Command):
    faction: Faction
    month: int


@dataclass(kw_only=True)
class EarnMonthlyFactionIncome(Command):
    faction: Faction
    month: int


@dataclass(kw_only=True)
class PrepareFactionWarriorsForMonth(Command):
    """
    Hand every man this faction is responsible for the month that has just turned.

    A read rather than a sweep, and deliberately unfiltered: what applies to a man is decided by the
    handlers subscribing to the event this raises, not here. That is what makes the event a fact - a
    filtered read could only announce a state somebody looked up.

    The faction's own roster plus the captives it holds, which is what "responsible for" means: a
    captive is on nobody's roster, capture having cleared "warrior.faction", so his captor's is the
    only month that can reach him.
    """

    faction: Faction
    month: int


@dataclass(kw_only=True)
class SetNewLeaderWarrior(Command):
    warrior: Warrior
    faction: Faction


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
