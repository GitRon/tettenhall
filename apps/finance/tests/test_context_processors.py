import pytest

from apps.faction.tests.factories.faction import FactionFactory
from apps.finance.context_processors import get_current_balance
from apps.finance.tests.factories.transaction import TransactionFactory
from apps.savegame.tests.factories.savegame import SavegameFactory


@pytest.mark.django_db
def test_get_current_balance_sums_up_the_transactions_of_the_player_faction(rf, user):
    savegame = SavegameFactory(created_by=user)
    savegame.player_faction = FactionFactory(savegame=savegame)
    savegame.save()
    TransactionFactory(faction=savegame.player_faction, amount=250)
    request = rf.get("/")
    request.user = user

    assert get_current_balance(request) == {"current_balance": 250}


@pytest.mark.django_db
def test_get_current_balance_ignores_the_transactions_of_rival_factions(rf, user):
    savegame = SavegameFactory(created_by=user)
    savegame.player_faction = FactionFactory(savegame=savegame)
    savegame.save()
    TransactionFactory(faction=savegame.player_faction, amount=250)
    TransactionFactory(faction=FactionFactory(savegame=savegame), amount=999)
    request = rf.get("/")
    request.user = user

    assert get_current_balance(request) == {"current_balance": 250}


@pytest.mark.django_db
def test_get_current_balance_without_a_player_faction(rf, savegame_without_player_faction, user):
    """
    The savegame row exists before its faction does, and this runs on every authenticated render, so
    it has to answer with an empty purse rather than dereference the missing faction. Leaving the key
    out is not an option: base.html renders the amount behind a "current_savegame" check only.
    """
    request = rf.get("/")
    request.user = user

    assert get_current_balance(request) == {"current_balance": 0}


@pytest.mark.django_db
def test_get_current_balance_without_an_active_savegame(rf, user):
    """
    A fresh account has no savegame yet. Without this the whole site - including the page that
    would create one - answers with a server error.
    """
    request = rf.get("/")
    request.user = user

    assert get_current_balance(request) == {"current_balance": 0}
