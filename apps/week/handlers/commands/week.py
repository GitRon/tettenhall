from queuebie import message_registry
from queuebie.messages import Event

from apps.training.models.training import Training
from apps.week.messages.commands.week import PrepareWeek
from apps.week.messages.events.week import WeekPrepared


@message_registry.register_command(command=PrepareWeek)
def handle_prepare_week(*, context: PrepareWeek) -> list[Event] | Event:
    # Increment current week
    current_week = context.savegame.current_week + 1
    context.savegame.current_week = current_week
    context.savegame.save()

    return WeekPrepared(
        marketplace=context.savegame.marketplace,
        faction=context.savegame.player_faction,
        # TODO: store this weeks training somewhere -> in savegame?
        training=Training.objects.all().first(),
        current_week=current_week,
    )
