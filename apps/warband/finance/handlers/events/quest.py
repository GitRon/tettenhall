from queuebie import message_registry
from queuebie.messages import Command

from apps.warband.calendar.months import get_calendar_month
from apps.warband.finance.messages.commands.transaction import CreateTransaction
from apps.warband.quest.messages.events.quest import QuestAccepted


@message_registry.register_event(event=QuestAccepted)
def handle_pay_march_cost_for_quest(*, context: QuestAccepted) -> Command | None:
    # An accepted quest musters the target's defenders exactly as a direct attack does, so it is the
    # same march and costs the same per man
    march_cost = get_calendar_month(month=context.month).get_march_cost(warrior_count=len(context.assigned_warriors))
    if not march_cost:
        return None

    return CreateTransaction(
        faction=context.accepting_faction,
        amount=-march_cost,
        reason=f"Winter march on {context.target_faction}",
        month=context.month,
    )
