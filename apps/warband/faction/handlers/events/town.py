from queuebie import message_registry
from queuebie.messages import Command

from apps.warband.faction.messages.commands.faction import ChangeFyrdReserve
from apps.warband.town.messages.events.town import GeldCalled


@message_registry.register_event(event=GeldCalled)
def handle_geld_strikes_names_off_the_fyrd(*, context: GeldCalled) -> Command:
    """
    What the village paid with. The command handler made sure the roll still held the names, so the
    reserve's floor at zero never swallows part of the strike.
    """
    return ChangeFyrdReserve(faction=context.faction, change=-context.fyrd_names, month=context.month)
