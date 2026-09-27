from queuebie import message_registry
from queuebie.messages import Command

from apps.warband.incident.messages.commands.incident import ChooseIncident
from apps.warband.incident.messages.commands.pending_incident import AnswerOpenPendingIncidents
from apps.warband.month.messages.events.month import PlayerMonthPrepared


@message_registry.register_event(event=PlayerMonthPrepared)
def handle_choose_incident_for_new_month(*, context: PlayerMonthPrepared) -> Command:
    """
    Every month rolls for an incident, and most months roll nothing.

    Registered on the player's month rather than on every faction's, which is the whole of what keeps
    a rival out of the chronicle: a rival has no log to read it in, and #3 has to give it an economy
    before an incident could mean anything to it. Moving this handler to FactionMonthPrepared is what
    that change would be.
    """
    return ChooseIncident(faction=context.faction, month=context.current_month)


@message_registry.register_event(event=PlayerMonthPrepared)
def handle_answer_open_pending_incidents_for_new_month(*, context: PlayerMonthPrepared) -> Command:
    """
    A question left open when the month ended is answered by its default.

    On the player's month, like the drawing: only the player is ever asked anything.
    """
    return AnswerOpenPendingIncidents(faction=context.faction, month=context.current_month)
