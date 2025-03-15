from dataclasses import dataclass

from queuebie.messages import Event

from apps.faction.models import Culture
from apps.faction.models.faction import Faction
from apps.skirmish.models.warrior import Warrior
from apps.warrior.services.generators.warrior.base import BaseWarriorGenerator


@dataclass(kw_only=True)
class RequestWarriorForPub(Event):
    faction: Faction | None
    # TODO: faction reicht nicht aus, ich möchte ja auch für andere factions des savegames warriors im pool haben
    culture: Culture
    generator_class: type[BaseWarriorGenerator]
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
