from dataclasses import dataclass

from queuebie.messages import Command

from apps.warband.faction.models.faction import Faction
from apps.warband.item.models.item import Item
from apps.warband.skirmish.choices.skirmish_action import SkirmishActionTypeHint
from apps.warband.skirmish.domain.action_roll import ActionRoll
from apps.warband.skirmish.models.skirmish import Skirmish
from apps.warband.skirmish.models.warrior import Warrior


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


@dataclass(kw_only=True)
class RecordSkirmishCasualty(Command):
    skirmish: Skirmish
    warrior: Warrior
    fate: int


@dataclass(kw_only=True)
class RecordSkirmishBlow(Command):
    skirmish: Skirmish
    round_number: int
    attacker: Warrior
    attacker_action: SkirmishActionTypeHint
    attack: ActionRoll
    defender: Warrior
    defender_action: SkirmishActionTypeHint
    defense: ActionRoll
    outcome: int
    damage: int = 0
