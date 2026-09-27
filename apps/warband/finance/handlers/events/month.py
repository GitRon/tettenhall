from queuebie import message_registry
from queuebie.messages import Command

from apps.warband.calendar.months import get_calendar_month
from apps.warband.finance.messages.commands.transaction import CreateTransaction
from apps.warband.month.messages.events.month import FactionMonthPrepared


# Every faction brings its harvest in, the rivals included: the fields are not the player's alone
@message_registry.register_event(event=FactionMonthPrepared)
def handle_bring_in_harvest_for_new_month(*, context: FactionMonthPrepared) -> Command | None:
    harvest_silver = get_calendar_month(month=context.current_month).HARVEST_SILVER
    if not harvest_silver:
        return None

    return CreateTransaction(
        faction=context.faction, amount=harvest_silver, reason="Harvest", month=context.current_month
    )
