from dataclasses import dataclass

from apps.core.event_loop.messages import Event
from apps.faction.models.faction import Faction
from apps.skirmish.models.warrior import Warrior


class WarriorRecruited(Event):
    @dataclass
    class Context:
        warrior: Warrior
        faction: Faction
        recruitment_price: int


class WarriorWasSoldIntoSlavery(Event):
    # todo refactor all "sell X" event and pass generic context string for transaction title
    @dataclass
    class Context:
        warrior: Warrior
        selling_faction: Faction
        price: int
