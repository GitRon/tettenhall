from dataclasses import dataclass

from queuebie.messages import Event

from apps.warband.faction.models.faction import Faction
from apps.warband.savegame.models.savegame import Savegame
from apps.warband.skirmish.models.warrior import Warrior
from apps.warband.town.models import Town


@dataclass(kw_only=True)
class NewFactionCreated(Event):
    """
    One faction and its town exist, and the savegame's opening hand can be dealt to it.

    "is_player" rides along because some of that hand is the player's alone, and every consumer is an
    event handler under strict mode's database blocker: comparing against "savegame.player_faction_id"
    would be a query, or a read of whichever relation happened to be cached.
    """

    faction: Faction
    current_month: int
    is_player: bool


@dataclass(kw_only=True)
class FactionWasDefeated(Event):
    """
    A faction lost the man who led it, had nobody left to take his seat, and is out of the game.

    Everything below the savegame rides along resolved, because every consumer is an event handler
    under strict mode's database blocker and none of them could look it up. "player_faction" is what
    the announcement is written against - the month log drops a line whose faction is not the
    player's, so passing the defeated rival there would write nothing at all. "leader" is the fallen
    man himself: capture clears his own faction, and reaching "faction.leader" downstream would be a
    lazy query for a warrior the raising handler already holds.
    """

    faction: Faction
    savegame: Savegame
    player_faction: Faction
    leader: Warrior
    # Which of the two blows it was. Resolved here rather than carried down from the skirmish, whose
    # handler is registered for the kill and the capture alike and may only read what both events have
    leader_was_killed: bool
    month: int


@dataclass(kw_only=True)
class FactionLeaderSucceeded(Event):
    """
    A faction lost the man who led it, and the man with the most renown on its roster took his seat.

    Carries the same resolved fields as [FactionWasDefeated], for the same reason: its consumers are
    event handlers and the fallen man may already have been cleared off his faction by a capture.
    """

    faction: Faction
    player_faction: Faction
    fallen_leader: Warrior
    successor: Warrior
    leader_was_killed: bool
    month: int


@dataclass(kw_only=True)
class FactionLeaderRaisedFromFyrd(Event):
    """
    A faction lost the man who led it with nobody left on its roster, and its fyrd raised a levy to lead
    it instead.

    Carries the same resolved fields as [FactionLeaderSucceeded], for the same reason. Kept apart from
    it because what happened is a different fact: the faction ran out of men and was saved by its land,
    not by the man next in line.
    """

    faction: Faction
    player_faction: Faction
    fallen_leader: Warrior
    successor: Warrior
    leader_was_killed: bool
    month: int


@dataclass(kw_only=True)
class FactionFyrdReserveReplenished(Event):
    faction: Faction
    new_recruits: int
    month: int


@dataclass(kw_only=True)
class FyrdReserveChanged(Event):
    """
    The reserve moved by something other than the monthly roll.

    Separate from FactionFyrdReserveReplenished rather than reusing it: that one is logged as "The
    fyrd has grown by ...", and the caller here has already written its own line about why.
    """

    faction: Faction
    change: int
    month: int


@dataclass(kw_only=True)
class MonthlyWarriorSalariesPaid(Event):
    faction: Faction
    amount: int
    month: int


@dataclass(kw_only=True)
class MonthlyWarriorSalariesUnpaid(Event):
    """
    The faction ran out of silver part way down its own payroll.

    Raised alongside MonthlyWarriorSalariesPaid rather than instead of it: a faction that covered
    three of its five men did both things in the same month.
    """

    faction: Faction
    # The men who went without, already carrying their updated "unpaid_months"
    warrior_list: list[Warrior]
    missing_amount: int
    month: int


@dataclass(kw_only=True)
class MonthlyBuildingMoneyEarned(Event):
    faction: Faction
    amount: int
    month: int


@dataclass(kw_only=True)
class TownBuildingUpgradeApproved(Event):
    """
    A rival has weighed its month and decided to raise the next level of one of its buildings.

    The level and its price ride along settled, because the whole decision was made before this was
    raised - which is what lets a rival build through the same UpgradeTownBuilding the player's town
    page dispatches.
    """

    faction: Faction
    town: Town
    building_type: str
    new_level: int
    costs: int
    month: int


@dataclass(kw_only=True)
class NewLeaderWarriorSet(Event):
    faction: Faction
    warrior: Warrior


@dataclass(kw_only=True)
class FactionWasOccupied(Event):
    """
    A rival town was ridden into, its treasury shared out and its leader seized where he stood.

    The leader and the silver both ride along already resolved. Everything reacting to this is an
    event handler under strict mode's database blocker, so neither the ledger nor the capture could
    look them up for itself.
    """

    faction: Faction
    occupying_faction: Faction
    leader: Warrior
    plundered_silver: int
    month: int


@dataclass(kw_only=True)
class FactionMonthPlanned(Event):
    """
    A faction has had its pick of what stood in its pub and on its shelf all month.

    Raised for every faction, the player included, because both monthly restocks hang off it: each
    clears its stock with a row delete, so it has to wait until whatever this faction chose to hire or
    buy has changed hands.
    """

    faction: Faction
    month: int
