from dataclasses import dataclass

from queuebie.messages import Command

from apps.warband.skirmish.models import Skirmish


@dataclass(kw_only=True)
class CreateBattleHistory(Command):
    skirmish: Skirmish
    message: str
