from queuebie import message_registry

from apps.month.messages.events.month import MonthPrepared
from apps.month.models import PlayerMonthLog


@message_registry.register_event(event=MonthPrepared)
def handle_close_all_previous_messages(*, context: MonthPrepared):
    PlayerMonthLog.objects.for_savegame(savegame_id=context.marketplace.savegame.id).filter(
        month__lt=context.current_month
    ).delete()
