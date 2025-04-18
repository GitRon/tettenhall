from dataclasses import dataclass

from queuebie.messages import Event

from apps.faction.models import Faction
from apps.quest.models import QuestContract
from apps.skirmish.choices.skirmish_action import SkirmishActionTypeHint
from apps.skirmish.models.skirmish import Skirmish
from apps.skirmish.models.warrior import Warrior


@dataclass(kw_only=True)
class SkirmishCreated(Event):
    skirmish: Skirmish
    quest_contract: QuestContract = None


@dataclass(kw_only=True)
class FighterPairsMatched(Event):
    skirmish: Skirmish
    warrior_1: Warrior
    warrior_2: Warrior
    attack_action_1: int
    attack_action_2: int


@dataclass(kw_only=True)
class AttackerDefenderDecided(Event):
    skirmish: Skirmish
    attacker: Warrior
    attacker_action: SkirmishActionTypeHint
    defender: Warrior
    defender_action: SkirmishActionTypeHint


@dataclass(kw_only=True)
class RoundFinished(Event):
    skirmish: Skirmish
    victor: Faction | None
    month: int


@dataclass(kw_only=True)
class SkirmishFinished(Event):
    skirmish: Skirmish
    incapacitated_warriors: list[Warrior]
    defeated_unconscious_warriors: list[Warrior]
    victorious_conscious_warriors: list[Warrior]
    quest_name: str
    quest_loot: int
    month: int
