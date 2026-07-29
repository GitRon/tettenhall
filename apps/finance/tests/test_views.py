import pytest
from django.urls import reverse

from apps.faction.tests.factories.faction import FactionFactory
from apps.finance.tests.factories.transaction import TransactionFactory
from apps.savegame.tests.factories.savegame import SavegameFactory


@pytest.mark.django_db
def test_transaction_list_view_lists_the_transactions_of_the_player_faction(logged_in_client, current_savegame):
    transaction = TransactionFactory(faction=current_savegame.player_faction, amount=250)

    response = logged_in_client.get(reverse("finance:transaction-list-view"))

    assert response.status_code == 200
    assert list(response.context["object_list"]) == [transaction]
    assert response.context["current_balance"] == 250


@pytest.mark.django_db
def test_transaction_list_view_hides_transactions_of_other_savegames(logged_in_client, current_savegame):
    other_savegame = SavegameFactory()
    other_savegame.player_faction = FactionFactory(savegame=other_savegame)
    other_savegame.save()
    TransactionFactory(faction=other_savegame.player_faction, amount=999)

    response = logged_in_client.get(reverse("finance:transaction-list-view"))

    assert response.status_code == 200
    assert list(response.context["object_list"]) == []
    assert response.context["current_balance"] == 0


@pytest.mark.django_db
def test_transaction_list_view_hides_the_transactions_of_rival_factions(logged_in_client, current_savegame):
    """
    The rivals of the very same savegame keep their own purses, so savegame scope is not enough.
    """
    TransactionFactory(faction=FactionFactory(savegame=current_savegame), amount=999)

    response = logged_in_client.get(reverse("finance:transaction-list-view"))

    assert list(response.context["object_list"]) == []
    assert response.context["current_balance"] == 0


@pytest.mark.django_db
def test_transaction_list_view_without_a_player_faction(logged_in_client, savegame_without_player_faction):
    """
    The savegame row exists before its faction does, so the page has to answer with an empty purse
    rather than dereference the missing faction.
    """
    response = logged_in_client.get(reverse("finance:transaction-list-view"))

    assert response.status_code == 200
    assert response.context["current_balance"] == 0


@pytest.mark.django_db
def test_transaction_list_view_without_an_active_savegame(logged_in_client):
    """
    The balance used to be read off the savegame unguarded, so the page answered with a 500.
    """
    response = logged_in_client.get(reverse("finance:transaction-list-view"))

    assert response.status_code == 200
    assert response.context["current_balance"] == 0
