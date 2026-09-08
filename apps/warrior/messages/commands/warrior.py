from dataclasses import dataclass

from queuebie.messages import Command

from apps.faction.models import Culture
from apps.faction.models.faction import Faction
from apps.savegame.models.savegame import Savegame
from apps.skirmish.models.warrior import Warrior
from apps.warrior.services.generators.warrior.base import BaseWarriorGenerator


@dataclass(kw_only=True)
class CreateWarrior(Command):
    savegame: Savegame
    faction: Faction
    culture: Culture
    generator_class: type[BaseWarriorGenerator]
    month: int


@dataclass(kw_only=True)
class CreateNewLeaderWarrior(Command):
    # TODO (#102): entweder mach ich alle so oder ich nutze hier das generische event mit generator_class?
    faction: Faction


@dataclass(kw_only=True)
class ReplenishWarriorMorale(Command):
    warrior: Warrior
    month: int


@dataclass(kw_only=True)
class PunishUnpaidWarrior(Command):
    warrior: Warrior
    # The faction that failed to pay him. Taken off the command rather than off the warrior because
    # the handler asks it who its leader is, and the warrior's own FK is what desertion clears
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
