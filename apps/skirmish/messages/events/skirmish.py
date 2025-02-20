from dataclasses import dataclass

from queuebie.messages import Event

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
    month: int


@dataclass(kw_only=True)
class SkirmishFinished(Event):
    skirmish: Skirmish
    month: int
