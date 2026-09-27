from dataclasses import dataclass

from queuebie.messages import Command

from apps.warband.skirmish.models import BattleHistory, Skirmish, Warrior


@dataclass(kw_only=True)
class CreateBattleHistory(Command):
    skirmish: Skirmish
    message: str
    # The line as the Saga tells it, and empty where the saga leaves the moment out. Defaulted because
    # most producers write no saga at all.
    saga: str = ""
    # Narration unless a producer says otherwise. Fifteen handlers write this command and three of
    # them are about a man going down, so the default is the case that does not have to be stated.
    kind: int = BattleHistory.KindChoices.KIND_NARRATION
    # Who the line is about, on the lines that are about somebody. Handed as the warrior rather than
    # as his faction so that the record decides whose man he was.
    warrior: Warrior | None = None
