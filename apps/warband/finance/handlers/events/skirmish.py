from queuebie import message_registry
from queuebie.messages import Command

from apps.warband.calendar.months import get_calendar_month
from apps.warband.finance.messages.commands.transaction import CreateTransaction
from apps.warband.skirmish.messages.events import transaction
from apps.warband.skirmish.messages.events.skirmish import FactionWasAttacked


@message_registry.register_event(event=transaction.WarriorDroppedSilver)
def handle_faction_loots_warriors_silver(*, context: transaction.WarriorDroppedSilver) -> Command | None:
    return CreateTransaction(
        faction=context.gaining_faction,
        # Income, so positive: the faction is the one gaining the silver, not paying it. Every
        # negative amount in the ledger is a cost - wages, recruitment, purchases, building work.
        # The victor's own fallen are in this list too, so this also covers their purse coming back
        # to their faction, the same way their gear does
        amount=context.amount,
        reason=f"Looted from {context.warrior}",
        month=context.month,
    )


@message_registry.register_event(event=FactionWasAttacked)
def handle_pay_march_cost_for_attack(*, context: FactionWasAttacked) -> Command | None:
    # Every man who marches is paid for, the leader among them. The price is the month's alone, so it
    # needs nothing this handler may not read; a month that charges nothing writes no ledger row
    march_cost = get_calendar_month(month=context.month).get_march_cost(warrior_count=len(context.attacking_warriors))
    if not march_cost:
        return None

    return CreateTransaction(
        faction=context.attacking_faction,
        amount=-march_cost,
        reason=f"Winter march on {context.defending_faction}",
        month=context.month,
    )
