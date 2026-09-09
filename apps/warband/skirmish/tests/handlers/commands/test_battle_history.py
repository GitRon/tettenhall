import pytest

from apps.warband.skirmish.handlers.commands.battle_history import handle_create_battle_history
from apps.warband.skirmish.messages.commands.battle_history import CreateBattleHistory
from apps.warband.skirmish.messages.events.battle_history import BattleHistoryCreated
from apps.warband.skirmish.models import BattleHistory
from apps.warband.skirmish.tests.factories.skirmish import SkirmishFactory


@pytest.mark.django_db
def test_handle_create_battle_history_writes_the_line_to_the_fight():
    skirmish = SkirmishFactory()

    result = handle_create_battle_history(context=CreateBattleHistory(skirmish=skirmish, message="Round 1 finished."))

    assert result == BattleHistoryCreated(history=BattleHistory.objects.get())
    assert BattleHistory.objects.get().skirmish == skirmish
