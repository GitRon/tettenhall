from queuebie import message_registry
from queuebie.messages import Command

from apps.marketplace.messages.commands.warrior import RestockPubMercenaries
from apps.month.messages.events.month import MonthPrepared


@message_registry.register_event(event=MonthPrepared)
def handle_restock_mercenaries_in_pub_for_new_month(*, context: MonthPrepared) -> list[Command]:
    return [RestockPubMercenaries(marketplace=context.marketplace, month=context.current_month)]
