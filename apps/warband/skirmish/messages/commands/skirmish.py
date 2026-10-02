from dataclasses import dataclass

from queuebie.messages import Command

from apps.warband.faction.models.faction import Faction
from apps.warband.skirmish.choices.raid_kind import RaidKindTypeHint
from apps.warband.skirmish.choices.skirmish_action import SkirmishActionTypeHint
from apps.warband.skirmish.models.skirmish import Skirmish
from apps.warband.skirmish.models.warrior import Warrior
from apps.warband.skirmish.projections.skirmish_participant import SkirmishParticipant


@dataclass(kw_only=True)
class AttackFaction(Command):
    attacking_faction: Faction
    target_faction: Faction
    assigned_warriors: list[Warrior]
    # A "RaidKindChoices" value: what the war band sets out to take
    raid_kind: RaidKindTypeHint
    month: int


@dataclass(kw_only=True)
class CreateSkirmish(Command):
    name: str
    faction_1: Faction
    faction_2: Faction
    warrior_list_1: list[Warrior]
    warrior_list_2: list[Warrior]
    # The men of the place among "warrior_list_2", recorded on the skirmish so its end knows whom to
    # send home
    local_warriors: list[Warrior]
    # A "RaidKindChoices" value, recorded on the skirmish so its end knows what a victory takes
    raid_kind: RaidKindTypeHint
    month: int
    # The wall the second faction fights behind. Zero unless whoever stages the fight says otherwise,
    # which is an open field
    fortification_strength: int = 0


@dataclass(kw_only=True)
class TakeRaidYield(Command):
    """
    Take what a won raid set out for from the faction it was won against: its silver, its fyrd.

    On top of the loot of the field, which every fight hands out whatever it was for. How much there is
    to take is a question for the database, so it is answered by the handler rather than carried here.
    """

    skirmish: Skirmish
    month: int


@dataclass(kw_only=True)
class SendLocalsHome(Command):
    """
    Release the men of the place who turned out for a fight and are still standing when it ends.

    The dead stay where they fell and the men about to be taken are the victor's - both are told apart
    from the fight's own end, which is why the men about to be captured travel with this.
    """

    skirmish: Skirmish
    defeated_unconscious_warriors: list[Warrior]
    month: int


@dataclass(kw_only=True)
class StartDuel(Command):
    skirmish: Skirmish
    skirmish_participants_1: list[SkirmishParticipant]
    skirmish_participants_2: list[SkirmishParticipant]


@dataclass(kw_only=True)
class DetermineAttacker(Command):
    skirmish: Skirmish
    round_number: int
    warrior_1: Warrior
    action_1: SkirmishActionTypeHint
    warrior_2: Warrior
    action_2: SkirmishActionTypeHint


@dataclass(kw_only=True)
class WarriorAttacksWarrior(Command):
    skirmish: Skirmish
    round_number: int
    attacker: Warrior
    attacker_action: SkirmishActionTypeHint
    defender: Warrior
    defender_action: SkirmishActionTypeHint
    # An "InitiativeChoices" value, passed through to the blow it becomes - see "WarriorTookDamage"
    initiative: int


@dataclass(kw_only=True)
class WarriorAssaultsFortification(Command):
    skirmish: Skirmish
    round_number: int
    warrior: Warrior


@dataclass(kw_only=True)
class FinishRound(Command):
    skirmish: Skirmish
    month: int


@dataclass(kw_only=True)
class WinSkirmish(Command):
    skirmish: Skirmish
    victorious_faction: Faction
    month: int
