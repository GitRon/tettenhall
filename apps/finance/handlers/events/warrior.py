from queuebie import message_registry
from queuebie.messages import Command

from apps.finance.messages.commands.transaction import CreateTransaction
from apps.warrior.messages.events.warrior import WarriorWasDismissed


@message_registry.register_event(event=WarriorWasDismissed)
def handle_pay_warrior_severance(*, context: WarriorWasDismissed) -> Command | None:
    """
    What the faction owes the man it sent away.

    The silver insolvency would have taken off it anyway, which is what makes letting a man go a
    decision rather than a free way out of a wage bill.

    Silent at nothing, the way "handle_warrior_recruited" is: a row reading "-0 silver" is not a
    payment, and a man on no wage is owed no wages.
    """
    if context.severance_pay == 0:
        return None

    return CreateTransaction(
        reason=f"Severance for {context.warrior}",
        amount=-context.severance_pay,
        faction=context.faction,
        month=context.month,
    )
