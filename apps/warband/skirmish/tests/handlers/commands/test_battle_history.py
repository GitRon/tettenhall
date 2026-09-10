import pytest

from apps.warband.skirmish.handlers.commands.battle_history import handle_create_battle_history
from apps.warband.skirmish.messages.commands.battle_history import CreateBattleHistory
from apps.warband.skirmish.messages.events.battle_history import BattleHistoryCreated
from apps.warband.skirmish.models import BattleHistory
from apps.warband.skirmish.tests.factories.skirmish import SkirmishFactory
from apps.warband.skirmish.tests.factories.warrior import WarriorFactory


@pytest.mark.django_db
def test_handle_create_battle_history_writes_the_line_to_the_fight():
    skirmish = SkirmishFactory()

    result = handle_create_battle_history(
        context=CreateBattleHistory(
            skirmish=skirmish, message="Round 1 finished.", kind=BattleHistory.KindChoices.KIND_NARRATION
        )
    )

    assert result == BattleHistoryCreated(history=BattleHistory.objects.get())
    assert BattleHistory.objects.get().skirmish == skirmish


@pytest.mark.django_db
def test_handle_create_battle_history_carries_the_kind_and_the_man_to_the_row():
    skirmish = SkirmishFactory()
    warrior = WarriorFactory(faction=skirmish.attacking_faction)

    handle_create_battle_history(
        context=CreateBattleHistory(
            skirmish=skirmish,
            message="Cuthred is out of the fight being killed.",
            kind=BattleHistory.KindChoices.KIND_WARRIOR_KILLED,
            warrior=warrior,
        )
    )

    record = BattleHistory.objects.get()
    assert record.kind == BattleHistory.KindChoices.KIND_WARRIOR_KILLED
    assert record.faction == skirmish.attacking_faction
