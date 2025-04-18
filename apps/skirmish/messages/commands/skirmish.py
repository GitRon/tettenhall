from dataclasses import dataclass

from django.db.models import QuerySet
from queuebie.messages import Command

from apps.faction.models.faction import Faction
from apps.quest.models import QuestContract
from apps.skirmish.choices.skirmish_action import SkirmishActionTypeHint
from apps.skirmish.models.skirmish import Skirmish
from apps.skirmish.models.warrior import Warrior
from apps.skirmish.projections.skirmish_participant import SkirmishParticipant


@dataclass(kw_only=True)
class CreateSkirmish(Command):
    name: str
    faction_1: Faction
    faction_2: Faction
    warrior_list_1: QuerySet[Warrior] | list[Warrior]
    warrior_list_2: QuerySet[Warrior] | list[Warrior] | None
    quest_contract: QuestContract = None


@dataclass(kw_only=True)
class StartDuel(Command):
    skirmish: Skirmish
    skirmish_participants_1: list[SkirmishParticipant]
    skirmish_participants_2: list[SkirmishParticipant]


@dataclass(kw_only=True)
class DetermineAttacker(Command):
    skirmish: Skirmish
    warrior_1: Warrior
    action_1: SkirmishActionTypeHint
    warrior_2: Warrior
    action_2: SkirmishActionTypeHint


@dataclass(kw_only=True)
class WarriorAttacksWarrior(Command):
    skirmish: Skirmish
    attacker: Warrior
    attacker_action: SkirmishActionTypeHint
    defender: Warrior
    defender_action: SkirmishActionTypeHint


@dataclass(kw_only=True)
class FinishRound(Command):
    skirmish: Skirmish
    month: int


@dataclass(kw_only=True)
class WinSkirmish(Command):
    skirmish: Skirmish
    victorious_faction: Faction
    month: int
