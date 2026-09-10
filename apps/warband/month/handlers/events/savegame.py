from queuebie import message_registry
from queuebie.messages import Command

from apps.warband.month.messages.commands.month import CreatePlayerMonthLog
from apps.warband.month.models.player_month_log import PlayerMonthLog
from apps.warband.savegame.messages.events.savegame import SavegameEnded
from apps.warband.savegame.models.savegame import Savegame


@message_registry.register_event(event=SavegameEnded)
def handle_log_savegame_ending(*, context: SavegameEnded) -> Command:
    """
    Says what the banner cannot: not that the game is over, but how it ended.

    The dashboard already carries the outcome, and until this line existed that was the whole of it -
    a savegame that ended in a lost fight said "Lost" over an empty log, with the answer sitting in a
    battle history the finished savegame no longer routes to.
    """
    if context.outcome == Savegame.OutcomeChoices.OUTCOME_WON:
        title = "The last rival has fallen."
        body = "No war band is left standing against you. The country is yours."
    else:
        title = "The war band is broken."
        body = "Your faction is out of the game, and what is left of it answers to nobody."

    return CreatePlayerMonthLog(
        title=title,
        body=body,
        kind=PlayerMonthLog.KindChoices.KIND_SAVEGAME_ENDED,
        month=context.month,
        faction=context.player_faction,
    )
