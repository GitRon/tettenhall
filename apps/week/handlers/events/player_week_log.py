from apps.core.domain import message_registry
from apps.week.messages.events.week import WeekPrepared
from apps.week.models import PlayerWeekLog


@message_registry.register_event(event=WeekPrepared)
def handle_close_all_previous_messages(*, context: WeekPrepared.Context):
    PlayerWeekLog.objects.for_savegame(savegame_id=context.marketplace.savegame.id).filter(
        week__lt=context.current_week
    ).delete()
