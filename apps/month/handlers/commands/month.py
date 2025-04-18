from queuebie import message_registry
from queuebie.messages import Event

from apps.month.messages.commands.month import ClearPlayerMonthLog, CreatePlayerMonthLog, PrepareMonth
from apps.month.messages.events.month import MonthPrepared, PlayerMonthLogCleared, PlayerMonthLogCreated
from apps.month.models import PlayerMonthLog
from apps.training.models.training import Training


@message_registry.register_command(command=PrepareMonth)
def handle_prepare_month(*, context: PrepareMonth) -> Event:
    # Increment current month
    current_month = context.savegame.current_month + 1
    context.savegame.current_month = current_month
    context.savegame.save()

    return MonthPrepared(
        faction=context.savegame.player_faction,
        savegame=context.savegame,
        # TODO: store this months training somewhere -> in savegame?
        training=Training.objects.all().first(),
        current_month=current_month,
    )


@message_registry.register_command(command=CreatePlayerMonthLog)
def handle_create_player_month_log(*, context: CreatePlayerMonthLog) -> Event:
    player_month_log = PlayerMonthLog.objects.create_record(
        title=context.title,
        month=context.month,
        faction_id=context.faction.id,
    )

    return PlayerMonthLogCreated(player_month_log=player_month_log)


@message_registry.register_command(command=ClearPlayerMonthLog)
def handle_clear_player_month_log(*, context: ClearPlayerMonthLog) -> Event:
    PlayerMonthLog.objects.for_savegame(savegame_id=context.savegame.id).filter(
        month__lt=context.current_month
    ).delete()

    return PlayerMonthLogCleared(savegame=context.savegame)
