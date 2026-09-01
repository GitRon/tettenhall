from dataclasses import dataclass

from queuebie.messages import Event

from apps.faction.models import Faction
from apps.quest.models import QuestContract
from apps.skirmish.choices.skirmish_action import SkirmishActionTypeHint
from apps.skirmish.models.skirmish import Skirmish
from apps.skirmish.models.warrior import Warrior


@dataclass(kw_only=True)
class FactionWasAttacked(Event):
    attacking_faction: Faction
    defending_faction: Faction
    # Both rosters arrive already resolved: whom the defender fields is a query, and the event
    # handler reacting to this is not allowed to run one
    attacking_warriors: list[Warrior]
    defending_warriors: list[Warrior]
    month: int


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
    # The round that just resolved, read off the skirmish before it is incremented. Carried rather
    # than looked up again, because by the time an event handler runs "current_round" has already
    # moved on to the round nobody has fought yet
    round_number: int
    victor: Faction | None
    month: int


@dataclass(kw_only=True)
class SkirmishFinished(Event):
    skirmish: Skirmish
    incapacitated_warriors: list[Warrior]
    defeated_unconscious_warriors: list[Warrior]
    victorious_healthy_warriors: list[Warrior]
    quest_name: str
    quest_loot: int
    month: int
