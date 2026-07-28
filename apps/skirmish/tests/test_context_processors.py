import pytest

from apps.savegame.tests.factories.savegame import SavegameFactory
from apps.skirmish.context_processors import get_open_skirmishes
from apps.skirmish.tests.factories.skirmish import SkirmishFactory


@pytest.mark.django_db
def test_get_open_skirmishes_returns_the_unresolved_skirmishes(rf, user):
    savegame = SavegameFactory(created_by=user)
    skirmish = SkirmishFactory(player_faction__savegame=savegame, victorious_faction=None)
    request = rf.get("/")
    request.user = user

    assert list(get_open_skirmishes(request)["open_skirmishes"]) == [skirmish]


@pytest.mark.django_db
def test_get_open_skirmishes_without_an_active_savegame(rf, user):
    """
    A fresh account has no savegame yet. Without this the whole site - including the page that
    would create one - answers with a server error.
    """
    request = rf.get("/")
    request.user = user

    assert get_open_skirmishes(request) == {}
