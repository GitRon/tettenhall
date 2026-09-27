from queuebie import message_registry
from queuebie.messages import Command

from apps.warband.calendar.months import get_calendar_month
from apps.warband.month.messages.commands.month import CreatePlayerMonthLog
from apps.warband.month.messages.events.month import FactionMonthPrepared
from apps.warband.month.models.player_month_log import PlayerMonthLog


# Raised for every faction because the harvest is; the command handler keeps the rivals' lines out of
# the player's log
@message_registry.register_event(event=FactionMonthPrepared)
def handle_log_harvest_for_new_month(*, context: FactionMonthPrepared) -> Command | None:
    harvest_silver = get_calendar_month(month=context.current_month).HARVEST_SILVER
    if not harvest_silver:
        return None

    return CreatePlayerMonthLog(
        title=f"The harvest is in, and it brought {harvest_silver} silver.",
        kind=PlayerMonthLog.KindChoices.KIND_HARVEST,
        month=context.current_month,
        faction=context.faction,
    )
