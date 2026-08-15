import pytest

from apps.month.models.player_month_log import PlayerMonthLog
from apps.month.tests.factories.player_month_log import PlayerMonthLogFactory
from apps.savegame.tests.factories.savegame import SavegameFactory


@pytest.mark.django_db
def test_for_player_faction_excludes_the_logs_of_rival_factions():
    """
    A savegame holds the player's faction plus its rivals, so scoping by savegame would still let
    the id from the URL reach a rival's log line.
    """
    savegame = SavegameFactory()
    player_month_log = PlayerMonthLogFactory(faction__savegame=savegame)
    PlayerMonthLogFactory(faction__savegame=savegame)

    result = PlayerMonthLog.objects.for_player_faction(faction_id=player_month_log.faction_id)

    assert list(result) == [player_month_log]
