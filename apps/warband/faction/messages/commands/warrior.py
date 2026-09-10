from dataclasses import dataclass

from queuebie.messages import Command

from apps.warband.faction.models.faction import Faction
from apps.warband.savegame.models.savegame import Savegame
from apps.warband.skirmish.models.warrior import Warrior


@dataclass(kw_only=True)
class RestockTownMercenaries(Command):
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
class DraftWarriorFromFyrd(Command):
    faction: Faction
    month: int


@dataclass(kw_only=True)
class ConsiderFyrdDraft(Command):
    """
    Asks whether this faction should call somebody up this month.

    A command because the answer is a query - who it is, what is in the reserve and what is in the
    purse - and the event handler on the monthly event may read none of those.
    """

    faction: Faction
    month: int


@dataclass(kw_only=True)
class RecruitPubMercenary(Command):
    """
    Take a mercenary standing in a faction's pub onto its roster, for his price.

    The warrior is the one thing this has to carry: the price is his own, so reading it off him in the
    handler is what keeps the guard the view applies and the row the ledger gets from naming two
    different numbers.
    """

    warrior: Warrior
    faction: Faction
    month: int


@dataclass(kw_only=True)
class PayMonthlyWarriorSalaries(Command):
    faction: Faction
    month: int
