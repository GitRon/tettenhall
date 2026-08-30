from dataclasses import dataclass

from queuebie.messages import Event

from apps.faction.models import Culture
from apps.faction.models.faction import Faction
from apps.savegame.models.savegame import Savegame
from apps.skirmish.models.warrior import Warrior
from apps.warrior.services.generators.warrior.base import BaseWarriorGenerator


@dataclass(kw_only=True)
class PubMercenarySlotOpened(Event):
    savegame: Savegame
    faction: Faction | None
    # TODO (#47): the faction alone is not enough - the pool should hold warriors for the other
    # factions of the savegame too
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
class WarriorRecruited(Event):
    warrior: Warrior
    faction: Faction
    recruitment_price: int
    month: int


@dataclass(kw_only=True)
class WarriorWasSoldIntoSlavery(Event):
    # TODO: refactor all "sell X" event and pass generic context string for transaction title
    warrior: Warrior
    selling_faction: Faction
    price: int
    month: int
