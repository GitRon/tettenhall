from queuebie import message_registry
from queuebie.messages import Event

from apps.month.messages.commands.month import PrepareMonth
from apps.month.messages.events.month import MonthPrepared
from apps.training.models.training import Training


@message_registry.register_command(command=PrepareMonth)
def handle_prepare_month(*, context: PrepareMonth) -> list[Event] | Event:
    # Increment current month
    current_month = context.savegame.current_month + 1
    context.savegame.current_month = current_month
    context.savegame.save()

    return MonthPrepared(
        faction=context.savegame.player_faction,
        # TODO: store this months training somewhere -> in savegame?
        training=Training.objects.all().first(),
        current_month=current_month,
    )
