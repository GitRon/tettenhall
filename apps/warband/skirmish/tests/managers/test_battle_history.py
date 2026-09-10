import pytest

from apps.warband.skirmish.models import BattleHistory
from apps.warband.skirmish.tests.factories.battle_history import BattleHistoryFactory
from apps.warband.skirmish.tests.factories.skirmish import SkirmishFactory
from apps.warband.skirmish.tests.factories.warrior import WarriorFactory


@pytest.mark.django_db
def test_create_record_files_the_line_under_the_side_the_man_fought_for():
    skirmish = SkirmishFactory()
    warrior = WarriorFactory(faction=skirmish.defending_faction)

    record = BattleHistory.objects.create_record(
        skirmish=skirmish,
        message="Cuthred is out of the fight being killed.",
        kind=BattleHistory.KindChoices.KIND_WARRIOR_KILLED,
        warrior=warrior,
    )

    assert record.kind == BattleHistory.KindChoices.KIND_WARRIOR_KILLED
    assert record.faction == skirmish.defending_faction


@pytest.mark.django_db
def test_create_record_leaves_a_line_about_nobody_without_a_side():
    skirmish = SkirmishFactory()

    record = BattleHistory.objects.create_record(
        skirmish=skirmish,
        message="Round 1 finished.",
        kind=BattleHistory.KindChoices.KIND_NARRATION,
    )

    assert record.kind == BattleHistory.KindChoices.KIND_NARRATION
    assert record.faction is None


@pytest.mark.django_db
def test_for_savegame_keeps_another_savegames_log_out():
    battle_history = BattleHistoryFactory()
    BattleHistoryFactory()
    savegame_id = battle_history.skirmish.attacking_faction.savegame_id

    result = BattleHistory.objects.for_savegame(savegame_id=savegame_id)

    assert list(result) == [battle_history]
