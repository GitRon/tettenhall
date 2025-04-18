from queuebie import message_registry
from queuebie.messages import Event

from apps.skirmish.messages.commands.battle_history import CreateBattleHistory
from apps.skirmish.messages.events.battle_history import BattleHistoryCreated
from apps.skirmish.models import BattleHistory


@message_registry.register_command(command=CreateBattleHistory)
def handle_faction_wins_skirmish(*, context: CreateBattleHistory) -> Event:
    history = BattleHistory.objects.create_record(
        skirmish=context.skirmish,
        message=context.message,
    )

    return BattleHistoryCreated(history=history)
