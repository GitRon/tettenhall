from queuebie import message_registry
from queuebie.messages import Event

from apps.warband.skirmish.messages.commands.battle_history import CreateBattleHistory
from apps.warband.skirmish.messages.events.battle_history import BattleHistoryCreated
from apps.warband.skirmish.models import BattleHistory


@message_registry.register_command(command=CreateBattleHistory)
def handle_create_battle_history(*, context: CreateBattleHistory) -> Event:
    history = BattleHistory.objects.create_record(
        skirmish=context.skirmish,
        message=context.message,
        kind=context.kind,
        warrior=context.warrior,
    )

    return BattleHistoryCreated(history=history)
