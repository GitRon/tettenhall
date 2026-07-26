import json

import pytest
from django.urls import reverse

from apps.finance.models import Transaction
from apps.item.tests.factories.item import ItemFactory
from apps.savegame.tests.factories.savegame import SavegameFactory


@pytest.mark.django_db
def test_item_sell_view_sells_the_item_of_the_player_faction(logged_in_client, current_savegame):
    """
    Flow test: no mocking inside the chain, so this runs the real queue and asserts the end state.
    """
    item = ItemFactory(savegame=current_savegame, owner=current_savegame.player_faction, price=120)

    response = logged_in_client.post(reverse("item:item-sell-view", kwargs={"pk": item.pk}))

    assert response.status_code == 200
    item.refresh_from_db()
    assert item.owner is None
    assert Transaction.objects.filter(faction=current_savegame.player_faction, amount=120).exists()


@pytest.mark.django_db
def test_item_sell_view_announces_the_changed_lists_to_htmx(logged_in_client, current_savegame):
    item = ItemFactory(savegame=current_savegame, owner=current_savegame.player_faction)

    response = logged_in_client.post(reverse("item:item-sell-view", kwargs={"pk": item.pk}))

    assert json.loads(response["HX-Trigger"]) == {"loadFactionItemList": "-", "loadFactionWarriorList": "-"}


@pytest.mark.django_db
def test_item_sell_view_cannot_sell_an_item_of_another_savegame(logged_in_client, current_savegame):
    """
    Without the savegame scoping the id from the URL would be enough to sell another player's item.
    """
    other_savegame = SavegameFactory()
    other_item = ItemFactory(savegame=other_savegame)

    response = logged_in_client.post(reverse("item:item-sell-view", kwargs={"pk": other_item.pk}))

    assert response.status_code == 404
    other_item.refresh_from_db()
    assert other_item.owner is None
