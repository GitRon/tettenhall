from queuebie import message_registry
from queuebie.messages import Command

from apps.warband.finance.messages.commands.transaction import CreateTransaction
from apps.warband.quest.messages.events.quest_contract import QuestContractReturned


@message_registry.register_event(event=QuestContractReturned)
def handle_quest_silver(*, context: QuestContractReturned) -> Command | None:
    """
    What the errand paid, for every man who came home from it.

    The chronicle line is the reason, the way an incident's is, so the ledger reads like the log.
    """
    amount = context.outcome.silver_per_man * len(context.warriors)
    if amount == 0:
        return None

    return CreateTransaction(
        faction=context.faction,
        amount=amount,
        reason=context.outcome.title,
        month=context.month,
    )
