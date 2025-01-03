from dataclasses import dataclass

from django.db.models import QuerySet

from apps.core.event_loop.messages import Command
from apps.faction.models.faction import Faction
from apps.quest.models import QuestContract
from apps.skirmish.models.skirmish import Skirmish
from apps.skirmish.models.warrior import Warrior
from apps.skirmish.projections.skirmish_participant import SkirmishParticipant


class CreateSkirmish(Command):
    @dataclass(kw_only=True)
    class Context:
        name: str
        faction_1: Faction
        faction_2: Faction
        warrior_list_1: QuerySet[Warrior] | list[Warrior]
        warrior_list_2: QuerySet[Warrior] | list[Warrior]
        quest_contract: QuestContract = None


class StartDuel(Command):
    @dataclass(kw_only=True)
    class Context:
        skirmish: Skirmish
        skirmish_participants_1: list[SkirmishParticipant]
        skirmish_participants_2: list[SkirmishParticipant]


class DetermineAttacker(Command):
    @dataclass(kw_only=True)
    class Context:
        skirmish: Skirmish
        warrior_1: Warrior
        action_1: int
        warrior_2: Warrior
        action_2: int


class WarriorAttacksWarriorWithSimpleAttack(Command):
    @dataclass(kw_only=True)
    class Context:
        skirmish: Skirmish
        attacker: Warrior
        defender: Warrior


class WarriorAttacksWarriorWithRiskyAttack(Command):
    @dataclass(kw_only=True)
    class Context:
        skirmish: Skirmish
        attacker: Warrior
        defender: Warrior


class WarriorAttacksWarriorWithFastAttack(Command):
    @dataclass(kw_only=True)
    class Context:
        skirmish: Skirmish
        attacker: Warrior
        defender: Warrior


class WinSkirmish(Command):
    @dataclass(kw_only=True)
    class Context:
        skirmish: Skirmish
        victorious_faction: Faction
