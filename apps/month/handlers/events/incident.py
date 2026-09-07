from queuebie import message_registry
from queuebie.messages import Command

from apps.incident.messages.events.incident import IncidentOccurred
from apps.month.messages.commands.month import CreatePlayerMonthLog
from apps.month.models.player_month_log import PlayerMonthLog


@message_registry.register_event(event=IncidentOccurred)
def handle_write_incident_to_month_log(*, context: IncidentOccurred) -> Command:
    """
    The only reaction every incident has: the player reads about it.

    One kind for all of them, so the chronicle is a weight in the log rather than a dozen kinds
    nobody groups by, and the body is the sentence the title had no room for.
    """
    return CreatePlayerMonthLog(
        title=context.outcome.title,
        body=context.outcome.body,
        kind=PlayerMonthLog.KindChoices.KIND_INCIDENT,
        month=context.month,
        faction=context.faction,
    )
