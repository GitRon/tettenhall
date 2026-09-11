from dataclasses import dataclass

from queuebie.messages import Event

from apps.warband.faction.models import Faction
from apps.warband.savegame.models.savegame import Savegame
from apps.warband.skirmish.models.warrior import Warrior


@dataclass(kw_only=True)
class WarriorMoraleReplenished(Event):
    warrior: Warrior
    faction: Faction
    recovered_morale: int
    month: int


@dataclass(kw_only=True)
class WarriorLostMoraleOverUnpaidSalary(Event):
    warrior: Warrior
    faction: Faction
    lost_morale: int
    month: int


@dataclass(kw_only=True)
class WarriorWalkedOutOverUnpaidSalary(Event):
    """
    Three months without wages and a man takes himself off the roster.

    Named for what he does rather than for desertion, which in this game is [CONDITION_FLEEING] - a
    rout he recovers from next month without ever leaving his faction. This is the other thing, and
    it is permanent.

    Carries the faction he walked out on, because his own FK is cleared by the time anybody reacts to
    this, and the savegame for the pub, which belongs to the player rather than to any faction on the
    message.
    """

    warrior: Warrior
    faction: Faction
    savegame: Savegame
    month: int


@dataclass(kw_only=True)
class WarriorWasDismissed(Event):
    """
    The player sent this man away.

    Carries the faction he was sent away from, because dismissal clears his own FK and by the time
    anybody reacts to this there is nothing on him left to log, bill or stock a pub against. The
    savegame comes along for the pub, which belongs to the player rather than to any faction on the
    message.

    The severance is on the event rather than read back off the warrior, the way [WarriorRecruited]
    carries its price: what the faction owes is fixed at the moment he goes, and the ledger row and
    the sentence the player reads have to name the same number.
    """

    warrior: Warrior
    faction: Faction
    savegame: Savegame
    severance_pay: int
    month: int


@dataclass(kw_only=True)
class WarriorMaxMoraleChanged(Event):
    """
    A warrior's morale ceiling moved for good.

    Carries the points it actually moved by rather than the share it was asked for: the share is
    truncated against what the man has, so what happened to a levy and to a veteran are different
    numbers.
    """

    warrior: Warrior
    faction: Faction
    changed_max_morale: int
    month: int


@dataclass(kw_only=True)
class WarriorEarnedNickname(Event):
    """
    The war band settled on what to call this man, and will not revise it.

    The epithet rides along as the phrasing he was given rather than as the state behind it, because
    what the player is told is the name: a consumer resolving the state itself would be a second place
    the wording is decided.

    The faction is on the event for the reason every warrior event carries one - whoever reacts is an
    event handler and may not go and ask.
    """

    warrior: Warrior
    faction: Faction
    nickname: str
    month: int


@dataclass(kw_only=True)
class WarriorHealthHealed(Event):
    warrior: Warrior
    faction: Faction
    healed_points: int
    month: int


@dataclass(kw_only=True)
class NewLeaderWarriorCreated(Event):
    warrior: Warrior
    faction: Faction


@dataclass(kw_only=True)
class WarriorCreated(Event):
    warrior: Warrior
    savegame: Savegame
    faction: Faction
    month: int
