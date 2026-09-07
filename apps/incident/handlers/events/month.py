from queuebie import message_registry
from queuebie.messages import Command

from apps.incident.messages.commands.incident import ChooseIncident
from apps.month.messages.events.month import PlayerMonthPrepared


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
