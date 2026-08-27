from dataclasses import dataclass

from queuebie.messages import Command

from apps.faction.models.faction import Faction


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
