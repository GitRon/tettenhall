from queuebie import message_registry
from queuebie.messages import Command

from apps.warband.month.messages.commands.month import ClearPlayerMonthLog
from apps.warband.month.messages.events.month import PlayerMonthPrepared


@message_registry.register_event(event=PlayerMonthPrepared)
def handle_close_all_previous_messages(*, context: PlayerMonthPrepared) -> Command:
    return ClearPlayerMonthLog(savegame=context.savegame, current_month=context.current_month)
