import pytest

from apps.warband.savegame.tests.factories.savegame import SavegameFactory
from apps.warband.town.models import Town
from apps.warband.town.tests.factories.town import TownFactory


@pytest.mark.django_db
def test_for_player_faction_excludes_the_towns_of_rival_factions():
    """
    A savegame holds the player's faction plus its rivals, so scoping by savegame would still let
    the town views reach a rival's town.
    """
    savegame = SavegameFactory()
    player_town = TownFactory(faction__savegame=savegame)
    TownFactory(faction__savegame=savegame)

    result = Town.objects.for_player_faction(faction_id=player_town.faction_id)

    assert list(result) == [player_town]
