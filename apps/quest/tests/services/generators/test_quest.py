import pytest

from apps.faction.tests.factories.faction import FactionFactory
from apps.quest.services.generators.quest import QuestGenerator
from apps.savegame.tests.factories.savegame import SavegameFactory


@pytest.mark.django_db
def test_process_targets_a_rival_faction():
    savegame = SavegameFactory()
    savegame.player_faction = FactionFactory(savegame=savegame)
    savegame.save()
    rival_faction = FactionFactory(savegame=savegame)

    quest = QuestGenerator(savegame=savegame).process()

    assert quest.target_faction == rival_faction
    assert quest.loot > 0


@pytest.mark.django_db
def test_process_without_a_player_faction():
    savegame = SavegameFactory()

    with pytest.raises(RuntimeError, match="has no player faction to create a quest for"):
        QuestGenerator(savegame=savegame).process()


@pytest.mark.django_db
def test_process_without_a_rival_faction():
    savegame = SavegameFactory()
    savegame.player_faction = FactionFactory(savegame=savegame)
    savegame.save()

    with pytest.raises(RuntimeError, match="has no rival faction a quest could target"):
        QuestGenerator(savegame=savegame).process()
