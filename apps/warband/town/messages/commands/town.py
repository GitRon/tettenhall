from dataclasses import dataclass

from queuebie.messages import Command

from apps.warband.faction.models import Faction
from apps.warband.skirmish.models.warrior import Warrior
from apps.warband.town.models import Town


@dataclass(kw_only=True)
class UpgradeTownBuilding(Command):
    town: Town
    faction: Faction
    building_type: str
    new_level: int
    costs: int
    month: int


@dataclass(kw_only=True)
class ThrowFeast(Command):
    """
    Sit the whole war band down in the hall, once this month.

    "warrior_list" is every man fed and "costs" what feeding them comes to, both settled by the view
    against the refusal it asked first. Unpaid men are on the list: they are fed and paid for, and it
    is the reaction mending the ceilings that leaves them out.
    """

    town: Town
    faction: Faction
    warrior_list: list[Warrior]
    restored_share: float
    costs: int
    month: int
