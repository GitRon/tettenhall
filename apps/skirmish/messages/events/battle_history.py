from dataclasses import dataclass

from queuebie.messages import Event

from apps.skirmish.models import BattleHistory


@dataclass(kw_only=True)
class BattleHistoryCreated(Event):
    history: BattleHistory
