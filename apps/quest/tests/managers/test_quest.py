import pytest

from apps.faction.tests.factories.faction import FactionFactory
from apps.quest.models.quest import Quest
from apps.quest.tests.factories.quest import QuestFactory
from apps.savegame.tests.factories.savegame import SavegameFactory


@pytest.mark.django_db
def test_for_player_faction_keeps_only_what_is_on_that_bulletin_board():
    """
    Every faction of a savegame gets its own quests offered, so the savegame is the wrong scope for
    singling out what the player was actually offered.
    """
    savegame = SavegameFactory()
    player_faction = FactionFactory(savegame=savegame)
    rival_faction = FactionFactory(savegame=savegame)

    offered_quest = QuestFactory(target_faction__savegame=savegame)
    player_faction.available_quests.add(offered_quest)
    rival_quest = QuestFactory(target_faction__savegame=savegame)
    rival_faction.available_quests.add(rival_quest)
    # In the savegame, but pinned to nobody's board
    QuestFactory(target_faction__savegame=savegame)

    assert list(Quest.objects.for_player_faction(faction_id=player_faction.id)) == [offered_quest]
