from queuebie import message_registry
from queuebie.messages import Event

from apps.faction.models.faction import Faction
from apps.month.messages.commands.month import ClearPlayerMonthLog, CreatePlayerMonthLog, PrepareMonth
from apps.month.messages.events.month import (
    FactionMonthPrepared,
    PlayerMonthLogCleared,
    PlayerMonthLogCreated,
    PlayerMonthPrepared,
)
from apps.month.models import PlayerMonthLog
from apps.training.models.training import Training


@message_registry.register_command(command=PrepareMonth)
def handle_prepare_month(*, context: PrepareMonth) -> list[Event]:
    # Increment current month
    current_month = context.savegame.current_month + 1
    context.savegame.current_month = current_month
    context.savegame.save()

    # Every faction of the savegame gets its month, the player's included - what each of them
    # actually does with it is decided by which handlers subscribe, not by who they are
    faction_list = Faction.objects.still_in_play(savegame_id=context.savegame.id)

    return [
        PlayerMonthPrepared(
            faction=context.savegame.player_faction,
            savegame=context.savegame,
            # TODO (#101): store this months training somewhere -> in savegame?
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
        *[FactionMonthPrepared(faction=faction, current_month=current_month) for faction in faction_list],
    ]


@message_registry.register_command(command=CreatePlayerMonthLog)
def handle_create_player_month_log(*, context: CreatePlayerMonthLog) -> Event | None:
    # Every faction of the savegame gets its month, so the recovery handlers emit this command for
    # the rivals too - and their lines would drown the player's own in his log. The producers cannot
    # tell them apart: they are event handlers, where strict mode's database blocker forbids the
    # traversal below. This command handler may query, and every producer passes through it.
    if context.faction.savegame.player_faction_id != context.faction.id:
        return None

    player_month_log = PlayerMonthLog.objects.create_record(
        title=context.title,
        month=context.month,
        faction_id=context.faction.id,
    )

    return PlayerMonthLogCreated(player_month_log=player_month_log)


@message_registry.register_command(command=ClearPlayerMonthLog)
def handle_clear_player_month_log(*, context: ClearPlayerMonthLog) -> Event:
    # Wider than the player faction on purpose, even though handle_create_player_month_log no longer
    # writes anything else: this is what sweeps up the rival rows a savegame accumulated before that
    # guard existed
    PlayerMonthLog.objects.for_savegame(savegame_id=context.savegame.id).filter(
        month__lt=context.current_month
    ).delete()

    return PlayerMonthLogCleared(savegame=context.savegame)
