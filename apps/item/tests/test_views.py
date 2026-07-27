import json

import pytest
from django.urls import reverse

from apps.faction.tests.factories.faction import FactionFactory
from apps.finance.models import Transaction
from apps.finance.tests.factories.transaction import TransactionFactory
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


@pytest.mark.django_db
def test_item_buy_view_buys_the_item_for_the_player_faction(logged_in_client, current_savegame):
    """
    Flow test: no mocking inside the chain, so this runs the real queue and asserts the end state.
    """
    TransactionFactory(faction=current_savegame.player_faction, amount=500)
    item = ItemFactory(savegame=current_savegame, price=120)
    current_savegame.player_faction.available_items.add(item)

    response = logged_in_client.post(reverse("item:item-buy-view", kwargs={"pk": item.pk}))

    assert response.status_code == 200
    item.refresh_from_db()
    assert item.owner == current_savegame.player_faction
    assert Transaction.objects.filter(faction=current_savegame.player_faction, amount=-120).exists()


@pytest.mark.django_db
def test_item_buy_view_announces_the_changed_shop_list_to_htmx(logged_in_client, current_savegame):
    TransactionFactory(faction=current_savegame.player_faction, amount=500)
    item = ItemFactory(savegame=current_savegame, price=120)

    response = logged_in_client.post(reverse("item:item-buy-view", kwargs={"pk": item.pk}))

    assert json.loads(response["HX-Trigger"]) == {"loadShopItemList": "-"}


@pytest.mark.django_db
def test_item_buy_view_refuses_to_buy_without_enough_silver(logged_in_client, current_savegame):
    """
    Only the player faction's transactions count towards the balance, so this stays below the price.
    """
    TransactionFactory(faction=current_savegame.player_faction, amount=50)
    item = ItemFactory(savegame=current_savegame, price=120)

    response = logged_in_client.post(reverse("item:item-buy-view", kwargs={"pk": item.pk}))

    assert response.status_code == 204
    assert json.loads(response["HX-Trigger"]) == {"notification": "You don't have enough money to buy this item."}
    item.refresh_from_db()
    assert item.owner is None


@pytest.mark.django_db
def test_item_buy_view_cannot_buy_an_item_of_another_savegame(logged_in_client, current_savegame):
    """
    Without the savegame scoping the id from the URL would be enough to take another player's item.
    """
    TransactionFactory(faction=current_savegame.player_faction, amount=500)
    other_savegame = SavegameFactory()
    other_item = ItemFactory(savegame=other_savegame, price=120)

    response = logged_in_client.post(reverse("item:item-buy-view", kwargs={"pk": other_item.pk}))

    assert response.status_code == 404
    other_item.refresh_from_db()
    assert other_item.owner is None


@pytest.mark.django_db
def test_item_sell_view_cannot_sell_an_item_of_a_rival_faction(logged_in_client, current_savegame):
    """
    Being in the same savegame is not enough - selling a rival's item would pay the rival.
    """
    rival_faction = FactionFactory(savegame=current_savegame)
    rival_item = ItemFactory(savegame=current_savegame, owner=rival_faction)

    response = logged_in_client.post(reverse("item:item-sell-view", kwargs={"pk": rival_item.pk}))

    assert response.status_code == 404
    rival_item.refresh_from_db()
    assert rival_item.owner == rival_faction


@pytest.mark.django_db
def test_item_buy_view_cannot_buy_an_item_that_is_not_on_sale(logged_in_client, current_savegame):
    """
    Only unowned items sit in the shop, so an owned one must not be buyable by id.
    """
    TransactionFactory(faction=current_savegame.player_faction, amount=500)
    rival_faction = FactionFactory(savegame=current_savegame)
    rival_item = ItemFactory(savegame=current_savegame, owner=rival_faction, price=120)

    response = logged_in_client.post(reverse("item:item-buy-view", kwargs={"pk": rival_item.pk}))

    assert response.status_code == 404
    rival_item.refresh_from_db()
    assert rival_item.owner == rival_faction
