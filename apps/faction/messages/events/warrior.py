from dataclasses import dataclass

from queuebie.messages import Event

from apps.faction.models import Culture
from apps.faction.models.faction import Faction
from apps.savegame.models.savegame import Savegame
from apps.skirmish.models.warrior import Warrior
from apps.warrior.services.generators.warrior.base import BaseWarriorGenerator


@dataclass(kw_only=True)
class RequestWarriorForPub(Event):
    # TODO: this is a command and not an event by name -> maybe just use commands? seems legit
    savegame: Savegame
    faction: Faction | None
    # TODO (#47): faction reicht nicht aus, ich möchte ja auch für andere factions des savegames warriors im pool haben
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
