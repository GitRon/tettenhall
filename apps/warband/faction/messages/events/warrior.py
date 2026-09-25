from dataclasses import dataclass

from queuebie.messages import Event

from apps.warband.faction.models import Culture
from apps.warband.faction.models.faction import Faction
from apps.warband.savegame.models.savegame import Savegame
from apps.warband.skirmish.models.warrior import Warrior
from apps.warband.warrior.services.generators.warrior.base import BaseWarriorGenerator


@dataclass(kw_only=True)
class PubMercenarySlotOpened(Event):
    """
    A stool in one faction's pub wants a man on it.

    Two factions, because for a pub mercenary they are genuinely different. "faction" is who the
    warrior will belong to, and that is nobody: he stands for hire. "pub_owner" is whose town he is
    standing in, and it rides along the whole chain to "AddWarriorToPub" so the man lands on that
    shelf rather than on whichever one the last hop could guess at.
    """

    savegame: Savegame
    faction: Faction | None
    pub_owner: Faction
    culture: Culture
    generator_class: type[BaseWarriorGenerator]
    month: int


@dataclass(kw_only=True)
class FyrdDraftApproved(Event):
    """
    This faction can call somebody up, and has decided to.

    The whole decision was made before this was raised, so the handler has nothing left to weigh -
    which is what lets a rival's draft run through the same DraftWarriorFromFyrd the player's fyrd
    card dispatches, rather than a second flow beside it.
    """

    faction: Faction
    month: int


@dataclass(kw_only=True)
class WarriorMonthPrepared(Event):
    """
    One man a faction is responsible for has entered a new month.

    The third level of the family [PlayerMonthPrepared] and [FactionMonthPrepared] open: the tick
    reaches a savegame, then each faction in it, then each man on each faction's books. Whatever
    recovery, decay or upkeep a month brings a warrior hangs off this, and what applies to him is
    decided by which handlers subscribe rather than by the read that raised it.

    The faction is the one holding him rather than the one he belongs to. A captive has none - capture
    clears "warrior.faction" - and he is mended at his captor's sanctuary and logged in his captor's
    month, neither of which a handler could read off him. A reaction that must not reach a prisoner
    compares his own "faction_id" against this one.
    """

    faction: Faction
    warrior: Warrior
    month: int


@dataclass(kw_only=True)
class PubMercenaryHireApproved(Event):
    """
    A rival has looked over its pub and decided to take this man.

    The whole decision was made before this was raised, so the handler has nothing left to weigh -
    which is what lets a rival's hire run through the same RecruitPubMercenary the player's pub
    dispatches, rather than a second flow beside it.
    """

    faction: Faction
    warrior: Warrior
    month: int


@dataclass(kw_only=True)
class PubHiringConsidered(Event):
    """
    A faction has had its pick of the shelf that stood in its pub all month.

    Raised for every faction, the player included, because it is what the monthly restock hangs off:
    the restock clears the shelf with a row delete, so it has to wait until whatever this faction
    chose to hire has been taken off it.
    """

    faction: Faction
    month: int


@dataclass(kw_only=True)
class WarriorRecruited(Event):
    warrior: Warrior
    faction: Faction
    recruitment_price: int
    month: int


@dataclass(kw_only=True)
class WarriorWasSoldIntoSlavery(Event):
    warrior: Warrior
    selling_faction: Faction
    price: int
    month: int


@dataclass(kw_only=True)
class WarriorWasAddedToPub(Event):
    pub_owner: Faction
    warrior: Warrior
    month: int


@dataclass(kw_only=True)
class TownMercenariesRestocked(Event):
    """
    The pub has been emptied and this month's mercenaries requested.

    Raised once for the whole restock, against WarriorWasAddedToPub firing per man - a line per man
    would bury the rest of the month.
    """

    faction: Faction
    new_mercenaries: int
    month: int
