import pytest
from django.urls import reverse

from apps.faction.tests.factories.faction import FactionFactory
from apps.finance.tests.factories.transaction import TransactionFactory
from apps.savegame.tests.factories.savegame import SavegameFactory


@pytest.mark.django_db
def test_transaction_list_view_lists_the_transactions_of_the_player_faction(logged_in_client, current_savegame):
    transaction = TransactionFactory(faction=current_savegame.player_faction, amount=250)

    response = logged_in_client.get(
        reverse("finance:transaction-list-view", kwargs={"faction_id": current_savegame.player_faction.id})
    )

    assert response.status_code == 200
    assert list(response.context["object_list"]) == [transaction]
    assert response.context["current_balance"] == 250


@pytest.mark.django_db
def test_transaction_list_view_hides_transactions_of_other_savegames(logged_in_client, current_savegame):
    other_savegame = SavegameFactory()
    other_savegame.player_faction = FactionFactory(savegame=other_savegame)
    other_savegame.save()
    TransactionFactory(faction=other_savegame.player_faction, amount=999)

    response = logged_in_client.get(
        reverse("finance:transaction-list-view", kwargs={"faction_id": current_savegame.player_faction.id})
    )

    assert response.status_code == 200
    assert list(response.context["object_list"]) == []
    assert response.context["current_balance"] == 0
