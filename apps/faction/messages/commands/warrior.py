from dataclasses import dataclass

from queuebie.messages import Command

from apps.faction.models.faction import Faction
from apps.skirmish.models.warrior import Warrior


@dataclass(kw_only=True)
class RestockTownMercenaries(Command):
    faction: Faction
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
