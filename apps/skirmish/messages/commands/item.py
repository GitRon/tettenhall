from dataclasses import dataclass

from queuebie.messages import Command

from apps.faction.models.faction import Faction
from apps.skirmish.models.skirmish import Skirmish
from apps.skirmish.models.warrior import Warrior


@dataclass(kw_only=True)
class WarriorDropsLoot(Command):
    skirmish: Skirmish
    warrior: Warrior
    new_owner: Faction
