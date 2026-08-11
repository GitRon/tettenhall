from queuebie import message_registry
from queuebie.messages import Event

from apps.faction.models.faction import Faction
from apps.month.messages.commands.month import ClearPlayerMonthLog, CreatePlayerMonthLog, PrepareMonth
from apps.month.messages.events.month import (
    MonthPrepared,
    PlayerMonthLogCleared,
    PlayerMonthLogCreated,
    RivalFactionMonthPrepared,
)
from apps.month.models import PlayerMonthLog
from apps.training.models.training import Training


@message_registry.register_command(command=PrepareMonth)
def handle_prepare_month(*, context: PrepareMonth) -> list[Event]:
    # Increment current month
    current_month = context.savegame.current_month + 1
    context.savegame.current_month = current_month
    context.savegame.save()

    # One event per rival next to the player's. Rivals only recover between months today; giving
    # them income or a restocked shop is a matter of stacking those handlers onto the event too,
    # see RivalFactionMonthPrepared
    rival_faction_list = Faction.objects.rivals_of(
        savegame_id=context.savegame.id, player_faction_id=context.savegame.player_faction_id
    )

    return [
        MonthPrepared(
            faction=context.savegame.player_faction,
            savegame=context.savegame,
            # TODO: store this months training somewhere -> in savegame?
            # Scoped to the player's own faction: every faction of the savegame owns a training row,
            # so scoping to the savegame would still train the player's warriors by whichever row
            # happens to come first. Stays None when there is no row - the consumer handles that.
            training=(
                Training.objects.for_player_faction(faction_id=context.savegame.player_faction_id).first()
                if context.savegame.player_faction_id
                else None
            ),
            current_month=current_month,
        ),
        *[
            RivalFactionMonthPrepared(faction=rival_faction, current_month=current_month)
            for rival_faction in rival_faction_list
        ],
    ]


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
