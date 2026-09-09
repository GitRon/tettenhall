from dataclasses import dataclass

from queuebie.messages import Event

from apps.warband.faction.models.faction import Faction
from apps.warband.skirmish.choices.skirmish_action import SkirmishActionTypeHint
from apps.warband.skirmish.domain.action_roll import ActionRoll
from apps.warband.skirmish.models.skirmish import Skirmish
from apps.warband.skirmish.models.warrior import Warrior


@dataclass(kw_only=True)
class LastUsedSkirmishActionStored(Event):
    skirmish: Skirmish
    warrior: Warrior
    skirmish_action: int


@dataclass(kw_only=True)
class WarriorTookDamage(Event):
    skirmish: Skirmish
    # Carried rather than read off the skirmish downstream, because "current_round" has already moved
    # on to the round nobody has fought yet by the time an event handler runs
    round_number: int
    attacker: Warrior
    attacker_action: SkirmishActionTypeHint
    # The whole swing rather than the single number it comes to: the die, and the value the fight
    # compared. A record holding only the second can never be read back as the first
    attack: ActionRoll
    defender: Warrior
    defender_action: SkirmishActionTypeHint
    defense: ActionRoll
    damage: int


@dataclass(kw_only=True)
class WarriorDefendedAllDamage(Event):
    skirmish: Skirmish
    round_number: int
    attacker: Warrior
    attacker_action: SkirmishActionTypeHint
    attack: ActionRoll
    defender: Warrior
    # Carried because turning a blow aside and simply standing there behind a shield are worth
    # opposite things to a warrior's nerve, and the damage alone cannot tell them apart
    defender_action: SkirmishActionTypeHint
    defense: ActionRoll
    # Which of the three ways nothing got through this was: a swing that went wide, an action that
    # threw nothing at all, or armour that took the whole blow
    outcome: int


@dataclass(kw_only=True)
class WarriorWasIncapacitated(Event):
    skirmish: Skirmish
    warrior: Warrior
    by_warrior: Warrior


@dataclass(kw_only=True)
class WarriorHasFled(Event):
    skirmish: Skirmish
    warrior: Warrior


@dataclass(kw_only=True)
class WarriorWasKilled(Event):
    skirmish: Skirmish
    warrior: Warrior
    by_warrior: Warrior


@dataclass(kw_only=True)
class WarriorWasCaptured(Event):
    # Nullable for the same reason as the command that raises it: an occupation takes a leader
    # without a fight, and there is no battle log for the line to be written into
    skirmish: Skirmish | None
    warrior: Warrior
    capturing_faction: Faction


@dataclass(kw_only=True)
class WarriorLostMorale(Event):
    skirmish: Skirmish
    warrior: Warrior
    lost_morale: int


@dataclass(kw_only=True)
class WarriorGainedMorale(Event):
    skirmish: Skirmish
    warrior: Warrior
    gained_morale: int


@dataclass(kw_only=True)
class WarriorGainedExperience(Event):
    skirmish: Skirmish
    warrior: Warrior
    gained_experience: int


@dataclass(kw_only=True)
class WarriorGainedLevel(Event):
    skirmish: Skirmish
    warrior: Warrior
    level: int


@dataclass(kw_only=True)
class WarriorImprovedStats(Event):
    skirmish: Skirmish
    warrior: Warrior
    gained_strength: int
    gained_dexterity: int
    gained_max_health: int
    gained_max_morale: int
    gained_salary: int
    # The wage *after* the growth, carried rather than read back off the warrior when the log line is
    # written. Every message in a level-up chain holds the same instance, so a gain crossing two
    # thresholds grows it twice before either log handler runs - and both lines would then quote the
    # wage the second growth left behind.
    new_monthly_salary: int
