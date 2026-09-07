from queuebie import message_registry
from queuebie.messages import Command

from apps.finance.messages.commands.transaction import CreateTransaction
from apps.incident.messages.events.incident import IncidentOccurred


@message_registry.register_event(event=IncidentOccurred)
def handle_incident_silver(*, context: IncidentOccurred) -> Command | None:
    """
    What the incident cost or brought, as a ledger row like any other.

    Refuses an incident that moves no silver: a lever an entry does not pull is left at its default,
    and most entries pull one or two of the four.

    The chronicle line is the reason, so the ledger reads the way the log does rather than as
    "Incident #7" - both columns hold at most 100 characters, so the one fits the other.
    """
    if context.outcome.silver_change == 0:
        return None

    return CreateTransaction(
        reason=context.outcome.title,
        amount=context.outcome.silver_change,
        faction=context.faction,
        month=context.month,
    )
