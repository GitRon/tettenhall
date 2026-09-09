from dataclasses import dataclass

from queuebie.messages import Command

from apps.warband.faction.models.faction import Faction
from apps.warband.skirmish.models.skirmish import Skirmish
from apps.warband.skirmish.models.warrior import Warrior


@dataclass(kw_only=True)
class WarriorDropsLoot(Command):
    skirmish: Skirmish
    warrior: Warrior
    new_owner: Faction
