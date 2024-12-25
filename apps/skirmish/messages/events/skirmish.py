from dataclasses import dataclass

from apps.core.event_loop.messages import Event
from apps.quest.models import QuestContract
from apps.skirmish.models.skirmish import Skirmish
from apps.skirmish.models.warrior import Warrior


class SkirmishCreated(Event):
    @dataclass(kw_only=True)
    class Context:
        skirmish: Skirmish
        quest_contract: QuestContract = None


class FighterPairsMatched(Event):
    @dataclass(kw_only=True)
    class Context:
        skirmish: Skirmish
        warrior_1: Warrior
        warrior_2: Warrior
        attack_action_1: int
        attack_action_2: int


class AttackerDefenderDecided(Event):
    @dataclass(kw_only=True)
    class Context:
        skirmish: Skirmish
        attacker: Warrior
        defender: Warrior
        attack_action: int


class RoundFinished(Event):
    @dataclass(kw_only=True)
    class Context:
        skirmish: Skirmish


class SkirmishFinished(Event):
    @dataclass(kw_only=True)
    class Context:
        skirmish: Skirmish
