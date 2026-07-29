import pytest
from django.urls import reverse

from apps.faction.tests.factories.faction import FactionFactory
from apps.finance.tests.factories.transaction import TransactionFactory


@pytest.mark.django_db
def test_transaction_list_view_lists_the_transactions_of_the_player_faction(logged_in_client, current_savegame):
    transaction = TransactionFactory(faction=current_savegame.player_faction, amount=250)

    response = logged_in_client.get(reverse("finance:transaction-list-view"))

    assert response.status_code == 200
    assert list(response.context["object_list"]) == [transaction]
    assert response.context["current_balance"] == 250


@pytest.mark.django_db
def test_transaction_list_view_hides_the_transactions_of_rival_factions(logged_in_client, current_savegame):
    """
    The scoping test for this view. The rivals of the very same savegame keep their own purses, so
    savegame scope is not enough here - which makes this the stricter case of a foreign savegame.
    """
    TransactionFactory(faction=FactionFactory(savegame=current_savegame), amount=999)

    response = logged_in_client.get(reverse("finance:transaction-list-view"))

    assert list(response.context["object_list"]) == []
    assert response.context["current_balance"] == 0
