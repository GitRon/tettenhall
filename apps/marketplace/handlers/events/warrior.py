from apps.core.domain import message_registry
from apps.core.event_loop.messages import Command
from apps.marketplace.messages.commands.warrior import RestockPubMercenaries
from apps.week.messages.events.week import WeekPrepared


@message_registry.register_event(event=WeekPrepared)
def handle_restock_mercenaries_in_pub_for_new_week(*, context: WeekPrepared.Context) -> list[Command]:
    return [
        RestockPubMercenaries(RestockPubMercenaries.Context(marketplace=context.marketplace, week=context.current_week))
    ]
