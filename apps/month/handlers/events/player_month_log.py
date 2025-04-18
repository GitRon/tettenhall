from queuebie import message_registry
from queuebie.messages import Command

from apps.month.messages.commands.month import ClearPlayerMonthLog
from apps.month.messages.events.month import MonthPrepared


@message_registry.register_event(event=MonthPrepared)
def handle_close_all_previous_messages(*, context: MonthPrepared) -> Command:
    return ClearPlayerMonthLog(savegame=context.savegame, current_month=context.current_month)
