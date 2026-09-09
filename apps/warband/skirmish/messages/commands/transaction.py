from dataclasses import dataclass

from queuebie.messages import Command

from apps.warband.faction.models.faction import Faction
from apps.warband.skirmish.models.skirmish import Skirmish
from apps.warband.skirmish.models.warrior import Warrior


@dataclass(kw_only=True)
class WarriorDropsSilver(Command):
    skirmish: Skirmish
    warrior: Warrior
    gaining_faction: Faction
    month: int
