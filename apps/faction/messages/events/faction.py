from dataclasses import dataclass

from queuebie.messages import Event

from apps.faction.models.faction import Faction
from apps.item.services.generators.item.base import BaseItemGenerator
from apps.quest.models import Quest
from apps.savegame.models.savegame import Savegame
from apps.skirmish.models.warrior import Warrior


@dataclass(kw_only=True)
class NewFactionCreated(Event):
    faction: Faction
    current_month: int


@dataclass(kw_only=True)
class FactionWasDefeated(Event):
    faction: Faction
    savegame: Savegame


@dataclass(kw_only=True)
class FactionFyrdReserveReplenished(Event):
    faction: Faction
    new_recruitees: int
    month: int


@dataclass(kw_only=True)
class MonthlyWarriorSalariesPaid(Event):
    faction: Faction
    amount: int
    month: int


@dataclass(kw_only=True)
class MonthlyWarriorSalariesUnpaid(Event):
    """
    The faction ran out of silver part way down its own payroll.

    Raised alongside MonthlyWarriorSalariesPaid rather than instead of it: a faction that covered
    three of its five men did both things in the same month.
    """

    faction: Faction
    # The men who went without, already carrying their updated "unpaid_months"
    warrior_list: list[Warrior]
    missing_amount: int
    month: int


@dataclass(kw_only=True)
class MonthlyBuildingMoneyEarned(Event):
    faction: Faction
    amount: int
    month: int


@dataclass(kw_only=True)
class MonthlyFactionIncomeEarned(Event):
    """
    A faction with no player behind it took its monthly income.

    Separate from MonthlyBuildingMoneyEarned rather than an amount passed through it: that one is
    logged as "Buildings earned ... silver this month", and a rival has no buildings to have earned
    it with.
    """

    faction: Faction
    amount: int
    month: int


@dataclass(kw_only=True)
class FactionWarriorsWithReducedMoraleDetermined(Event):
    faction: Faction
    warrior_list: list[Warrior]
    month: int


@dataclass(kw_only=True)
class NewLeaderWarriorSet(Event):
    faction: Faction
    warrior: Warrior


@dataclass(kw_only=True)
class RequestNewItemForTownShop(Event):
    # TODO: item.py?
    faction: Faction
    generator_class: type[BaseItemGenerator]
    item_function: int
    month: int
    quality_bonus: int = 0


@dataclass(kw_only=True)
class WarriorWasAddedToPub(Event):
    # TODO: warrior.py?
    faction: Faction
    warrior: Warrior
    month: int


@dataclass(kw_only=True)
class QuestWasRemovedFromBulletinBoard(Event):
    # TODO: quest.py?
    faction: Faction
    quest: Quest
    month: int


@dataclass(kw_only=True)
class FactionWasOccupied(Event):
    """
    A rival town was ridden into, its treasury shared out and its leader seized where he stood.

    The leader and the silver both ride along already resolved. Everything reacting to this is an
    event handler under strict mode's database blocker, so neither the ledger nor the capture could
    look them up for itself.
    """

    faction: Faction
    occupying_faction: Faction
    leader: Warrior
    plundered_silver: int
    month: int
