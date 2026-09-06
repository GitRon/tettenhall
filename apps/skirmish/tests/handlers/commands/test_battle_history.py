import pytest

from apps.skirmish.handlers.commands.battle_history import handle_create_battle_history
from apps.skirmish.messages.commands.battle_history import CreateBattleHistory
from apps.skirmish.messages.events.battle_history import BattleHistoryCreated
from apps.skirmish.models import BattleHistory
from apps.skirmish.tests.factories.skirmish import SkirmishFactory


@pytest.mark.django_db
def test_handle_create_battle_history_writes_the_line_to_the_fight():
    skirmish = SkirmishFactory()

    result = handle_create_battle_history(context=CreateBattleHistory(skirmish=skirmish, message="Round 1 finished."))

    assert result == BattleHistoryCreated(history=BattleHistory.objects.get())
    assert BattleHistory.objects.get().skirmish == skirmish
