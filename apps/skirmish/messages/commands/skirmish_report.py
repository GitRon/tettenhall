from dataclasses import dataclass

from queuebie.messages import Command

from apps.faction.models.faction import Faction
from apps.item.models.item import Item
from apps.skirmish.models.skirmish import Skirmish
from apps.skirmish.models.warrior import Warrior


@dataclass(kw_only=True)
class RecordSkirmishSpoil(Command):
    skirmish: Skirmish
    faction: Faction
    kind: int
    item: Item = None
    warrior: Warrior = None
    amount: int = 0
    description: str = ""


@dataclass(kw_only=True)
class RecordWarriorGrowth(Command):
    skirmish: Skirmish
    warrior: Warrior
    gained_experience: int = 0
    reached_level: int = None
    gained_strength: int = 0
    gained_dexterity: int = 0
    gained_max_health: int = 0
    gained_max_morale: int = 0
    new_monthly_salary: int = None
