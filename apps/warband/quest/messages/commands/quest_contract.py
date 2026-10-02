from dataclasses import dataclass

from queuebie.messages import Command

from apps.warband.faction.models.faction import Faction


@dataclass(kw_only=True)
class BringQuestContractsHome(Command):
    faction: Faction
    month: int
