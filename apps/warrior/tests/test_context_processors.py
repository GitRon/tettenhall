import pytest

from apps.faction.tests.factories.faction import FactionFactory
from apps.savegame.tests.factories.savegame import SavegameFactory
from apps.skirmish.tests.factories.warrior import WarriorFactory
from apps.warrior.context_processors import get_current_amount_warriors


@pytest.mark.django_db
def test_get_current_amount_warriors_returns_the_living_warriors_of_the_player_faction(rf, user):
    savegame = SavegameFactory(created_by=user)
    savegame.player_faction = FactionFactory(savegame=savegame)
    savegame.save()
    warrior = WarriorFactory(faction=savegame.player_faction)
    request = rf.get("/")
    request.user = user

    assert list(get_current_amount_warriors(request)["faction_warriors"]) == [warrior]


@pytest.mark.django_db
def test_get_current_amount_warriors_without_an_active_savegame(rf, user):
    """
    A fresh account has no savegame yet. Without this the whole site - including the page that
    would create one - answers with a server error.
    """
    request = rf.get("/")
    request.user = user

    assert list(get_current_amount_warriors(request)["faction_warriors"]) == []


@pytest.mark.django_db
def test_get_current_amount_warriors_without_a_player_faction(rf, user):
    """
    A savegame carries no player faction until one has been created for it. Leaving the key out is
    not an option: base.html renders the count behind a "current_savegame" check only, so the navbar
    would show a warrior icon followed by nothing.
    """
    SavegameFactory(created_by=user, player_faction=None)
    request = rf.get("/")
    request.user = user

    assert list(get_current_amount_warriors(request)["faction_warriors"]) == []
