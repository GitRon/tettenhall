from queuebie import message_registry
from queuebie.messages import Event

from apps.warband.incident.incidents import INCIDENTS_BY_NAME
from apps.warband.incident.incidents.base import IncidentOption
from apps.warband.incident.messages.commands.pending_incident import AnswerOpenPendingIncidents, AnswerPendingIncident
from apps.warband.incident.messages.events.incident import IncidentOccurred
from apps.warband.incident.models.pending_incident import PendingIncident


@message_registry.register_command(command=AnswerPendingIncident)
def handle_answer_pending_incident(*, context: AnswerPendingIncident) -> Event:
    """
    Land the answer the player gave, and close the question.

    The answer raises the same event an ordinary incident does, so the levers and the chronicle line
    apply through the handlers every incident already has.
    """
    return _answer(pending_incident=context.pending_incident, option=context.option, month=context.month)


@message_registry.register_command(command=AnswerOpenPendingIncidents)
def handle_answer_open_pending_incidents(*, context: AnswerOpenPendingIncidents) -> list[Event]:
    """
    Every question the player left open when his month ended takes its default answer.

    Only those asked before the month now beginning: this month's incident may just have asked a new
    question, and that one is the player's to answer. The answer is dated to the new month, so the
    line it writes survives the log clearing and the player reads what his silence decided.
    """
    open_incidents = PendingIncident.objects.for_player_faction(faction_id=context.faction.id).asked_before(
        month=context.month
    )

    return [
        _answer(
            pending_incident=pending_incident,
            option=INCIDENTS_BY_NAME[pending_incident.incident].get_default_option(),
            month=context.month,
        )
        for pending_incident in open_incidents.select_related("faction", "rival", "item__type")
    ]


def _answer(*, pending_incident: PendingIncident, option: IncidentOption, month: int) -> IncidentOccurred:
    # Resolved before the row goes: the answer reads the rival and the gear the question was about
    outcome = INCIDENTS_BY_NAME[pending_incident.incident].answer(option=option, pending_incident=pending_incident)
    pending_incident.delete()

    return IncidentOccurred(faction=pending_incident.faction, month=month, outcome=outcome)
