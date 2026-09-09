from dataclasses import dataclass

from queuebie.messages import Event

from apps.warband.skirmish.models import BattleHistory


@dataclass(kw_only=True)
class BattleHistoryCreated(Event):
    history: BattleHistory
