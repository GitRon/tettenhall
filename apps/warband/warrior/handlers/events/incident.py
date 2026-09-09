from queuebie import message_registry
from queuebie.messages import Command

from apps.warband.incident.messages.events.incident import IncidentOccurred
from apps.warband.warrior.messages.commands.warrior import ChangeWarriorMaxMorale


@message_registry.register_event(event=IncidentOccurred)
def handle_incident_max_morale(*, context: IncidentOccurred) -> Command | None:
    """
    A permanent change to one man's morale ceiling.

    Keyed on the share rather than on the warrior: an entry may name a man for its title without
    touching his nerve, so the man an incident happened to is not always the lever it pulls.
    """
    if context.outcome.max_morale_share == 0:
        return None

    return ChangeWarriorMaxMorale(
        warrior=context.outcome.warrior,
        faction=context.faction,
        share=context.outcome.max_morale_share,
        month=context.month,
    )
