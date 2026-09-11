from dataclasses import dataclass

from queuebie.messages import Command

from apps.warband.faction.models import Culture
from apps.warband.faction.models.faction import Faction
from apps.warband.savegame.models.savegame import Savegame
from apps.warband.skirmish.models.warrior import Warrior
from apps.warband.warrior.services.generators.warrior.base import BaseWarriorGenerator


@dataclass(kw_only=True)
class CreateWarrior(Command):
    savegame: Savegame
    faction: Faction
    culture: Culture
    generator_class: type[BaseWarriorGenerator]
    month: int


@dataclass(kw_only=True)
class CreateNewLeaderWarrior(Command):
    # What a creation command carries is decided by what its producer is allowed to read, not by the
    # kind of warrior it makes. This one is raised by an event handler that has nothing but the
    # faction - strict mode forbids it the traversal to the culture and the savegame - so its own
    # handler resolves them, where a query is allowed. "CreateWarrior" carries them already resolved
    # because the event its producer reacts to was given them by a command handler that could query.
    faction: Faction


@dataclass(kw_only=True)
class ReplenishWarriorMorale(Command):
    warrior: Warrior
    month: int


@dataclass(kw_only=True)
class PunishUnpaidWarrior(Command):
    warrior: Warrior
    # The faction that failed to pay him. Taken off the command rather than off the warrior because
    # the handler asks it who its leader is, and the warrior's own FK is what walking out clears
    faction: Faction
    month: int


@dataclass(kw_only=True)
class ChangeWarriorMaxMorale(Command):
    """
    Move the ceiling a warrior's morale is measured against, permanently.

    A share rather than a number of points, so a levy and a veteran are asked for the same fraction
    of what they have. Signed: the same lever raises and lowers, and the caller pricing both against
    each other is what keeps a permanent change from drifting one way over a savegame.

    The ceiling and not "current_morale" on purpose. The monthly sweep refills every warrior to his
    maximum, so a change to the current value made early in a month is erased before the month ends.
    """

    warrior: Warrior
    faction: Faction
    share: float
    month: int


@dataclass(kw_only=True)
class AwardEarnedNickname(Command):
    """
    Ask whether this man has just become somebody worth naming.

    Raised wherever an attribute goes up, and a no-op for the men it does not apply to, so the two
    places that move one do not have to know the rule. The faction is not on it: the line the player
    reads needs one, and a command handler may look it up where an event handler may not.
    """

    warrior: Warrior
    month: int


@dataclass(kw_only=True)
class HealInjuredWarrior(Command):
    # The faction mending him, which is not always the one he belongs to: a captive is healed by the
    # faction holding him, and capture has cleared his own
    faction: Faction
    warrior: Warrior
    month: int


@dataclass(kw_only=True)
class RecruitCapturedWarrior(Command):
    warrior: Warrior
    faction: Faction
    month: int


@dataclass(kw_only=True)
class EnslaveCapturedWarrior(Command):
    warrior: Warrior
    faction: Faction
    month: int


@dataclass(kw_only=True)
class DismissWarrior(Command):
    """
    Send a warrior away, off the roster and out of the gear the faction paid for.

    The savegame rides along because the pub he ends up standing in is the player's, and the handler
    reacting to this may not look one up. The faction is carried for the same reason
    [PunishUnpaidWarrior] carries it: the handler asks it who its leader is, and his own FK is what
    this clears.
    """

    warrior: Warrior
    faction: Faction
    savegame: Savegame
    month: int
