from queuebie import message_registry
from queuebie.messages import Command

from apps.faction.messages.commands.faction import ChangeFyrdReserve
from apps.incident.messages.events.incident import IncidentOccurred


@message_registry.register_event(event=IncidentOccurred)
def handle_incident_fyrd_reserve(*, context: IncidentOccurred) -> Command | None:
    """
    Men the incident brought in or took away, added to the reserve or taken off it.

    The amount is the entry's, already clamped to what the reserve holds where that matters - see
    FeverInTheVillages.
    """
    if context.outcome.fyrd_change == 0:
        return None

    return ChangeFyrdReserve(
        faction=context.faction,
        change=context.outcome.fyrd_change,
        month=context.month,
    )
