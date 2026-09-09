from dataclasses import dataclass

from queuebie.messages import Command

from apps.warband.faction.models import Faction


@dataclass(kw_only=True)
class OfferNewQuestsOnBulletinBoard(Command):
    faction: Faction
    month: int
