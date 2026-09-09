from queuebie import message_registry
from queuebie.messages import Command

from apps.warband.incident.messages.events.incident import IncidentOccurred
from apps.warband.item.messages.commands.item import LoseItem


@message_registry.register_event(event=IncidentOccurred)
def handle_incident_lost_item(*, context: IncidentOccurred) -> Command | None:
    """
    The gear an incident swallowed, on its way out of the game.

    Which piece it is was settled when the incident resolved - see MoorLostGear, which never picks
    the finest weapon or the finest armour in the field.
    """
    if context.outcome.lost_item is None:
        return None

    return LoseItem(
        faction=context.faction,
        item=context.outcome.lost_item,
        month=context.month,
    )
