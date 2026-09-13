import json

import pytest
from django.urls import reverse

from apps.warband.faction.tests.factories.faction import FactionFactory
from apps.warband.finance.models import Transaction
from apps.warband.finance.tests.factories.transaction import TransactionFactory
from apps.warband.item.models.item_type import ItemType
from apps.warband.item.tests.factories.item import ItemFactory
from apps.warband.item.tests.factories.item_type import ItemTypeFactory
from apps.warband.savegame.tests.factories.savegame import SavegameFactory
from apps.warband.skirmish.tests.factories.warrior import WarriorFactory


@pytest.mark.django_db
def test_item_sell_view_sells_the_item_of_the_player_faction(logged_in_client, current_savegame):
    """
    Flow test: no mocking inside the chain, so this runs the real queue and asserts the end state.
    """
    item = ItemFactory(savegame=current_savegame, owner=current_savegame.player_faction, price=120)

    response = logged_in_client.post(reverse("warband:item-sell-view", kwargs={"pk": item.pk}))

    assert response.status_code == 200
    item.refresh_from_db()
    assert item.owner is None
    # A town without a market of its own only gets 40% of the list price
    assert Transaction.objects.filter(faction=current_savegame.player_faction, amount=48).exists()


@pytest.mark.django_db
def test_item_sell_view_announces_the_changed_lists_to_htmx(logged_in_client, current_savegame):
    item = ItemFactory(savegame=current_savegame, owner=current_savegame.player_faction)

    response = logged_in_client.post(reverse("warband:item-sell-view", kwargs={"pk": item.pk}))

    assert json.loads(response["HX-Trigger"]) == {
        "loadFactionItemList": "-",
        "loadFactionWarriorList": "-",
        "updateResourceBar": "-",
    }


@pytest.mark.django_db
def test_item_sell_view_cannot_sell_an_item_of_another_savegame(logged_in_client, current_savegame):
    """
    Without the savegame scoping the id from the URL would be enough to sell another player's item.
    """
    other_savegame = SavegameFactory()
    other_item = ItemFactory(savegame=other_savegame)

    response = logged_in_client.post(reverse("warband:item-sell-view", kwargs={"pk": other_item.pk}))

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

    response = logged_in_client.post(reverse("warband:item-buy-view", kwargs={"pk": item.pk}))

    assert response.status_code == 200
    item.refresh_from_db()
    assert item.owner == current_savegame.player_faction
    assert Transaction.objects.filter(faction=current_savegame.player_faction, amount=-120).exists()


@pytest.mark.django_db
def test_item_buy_view_announces_the_changed_shop_list_to_htmx(logged_in_client, current_savegame):
    TransactionFactory(faction=current_savegame.player_faction, amount=500)
    item = ItemFactory(savegame=current_savegame, price=120)
    current_savegame.player_faction.available_items.add(item)

    response = logged_in_client.post(reverse("warband:item-buy-view", kwargs={"pk": item.pk}))

    assert json.loads(response["HX-Trigger"]) == {"loadShopItemList": "-", "updateResourceBar": "-"}


@pytest.mark.django_db
def test_item_buy_view_refuses_to_buy_without_enough_silver(logged_in_client, current_savegame):
    """
    Only the player faction's transactions count towards the balance, so this stays below the price.
    """
    TransactionFactory(faction=current_savegame.player_faction, amount=50)
    item = ItemFactory(savegame=current_savegame, price=120)
    current_savegame.player_faction.available_items.add(item)

    response = logged_in_client.post(reverse("warband:item-buy-view", kwargs={"pk": item.pk}))

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

    response = logged_in_client.post(reverse("warband:item-buy-view", kwargs={"pk": other_item.pk}))

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

    response = logged_in_client.post(reverse("warband:item-sell-view", kwargs={"pk": rival_item.pk}))

    assert response.status_code == 404
    rival_item.refresh_from_db()
    assert rival_item.owner == rival_faction


@pytest.mark.django_db
def test_item_buy_view_cannot_buy_an_item_that_is_not_on_sale(logged_in_client, current_savegame):
    """
    An item somebody owns is not on the shop shelf, so it must not be buyable by id.
    """
    TransactionFactory(faction=current_savegame.player_faction, amount=500)
    rival_faction = FactionFactory(savegame=current_savegame)
    rival_item = ItemFactory(savegame=current_savegame, owner=rival_faction, price=120)

    response = logged_in_client.post(reverse("warband:item-buy-view", kwargs={"pk": rival_item.pk}))

    assert response.status_code == 404
    rival_item.refresh_from_db()
    assert rival_item.owner == rival_faction


@pytest.mark.django_db
def test_item_buy_view_cannot_buy_the_equipment_of_a_pub_mercenary(logged_in_client, current_savegame):
    """
    "Unowned" is not the same as "for sale": a mercenary waiting in the pub carries its weapons
    without a faction owning them, and buying one of those disarms the mercenary.
    """
    TransactionFactory(faction=current_savegame.player_faction, amount=500)
    mercenary_weapon = ItemFactory(savegame=current_savegame, owner=None, price=120)

    response = logged_in_client.post(reverse("warband:item-buy-view", kwargs={"pk": mercenary_weapon.pk}))

    assert response.status_code == 404
    mercenary_weapon.refresh_from_db()
    assert mercenary_weapon.owner is None


@pytest.mark.django_db
def test_item_buy_view_without_a_player_faction(logged_in_client, savegame_without_player_faction):
    """
    There is no shop to buy from yet, and the shelf lookup needs a faction id - so this narrows to
    nothing rather than answering with a server error.
    """
    item = ItemFactory(savegame=savegame_without_player_faction, price=120)

    response = logged_in_client.post(reverse("warband:item-buy-view", kwargs={"pk": item.pk}))

    assert response.status_code == 404
    item.refresh_from_db()
    assert item.owner is None


@pytest.mark.django_db
def test_item_sell_view_without_a_player_faction(logged_in_client, savegame_without_player_faction):
    """
    Nothing belongs to the player yet, so the player-faction scoping narrows to nothing.
    """
    item = ItemFactory(savegame=savegame_without_player_faction)

    response = logged_in_client.post(reverse("warband:item-sell-view", kwargs={"pk": item.pk}))

    assert response.status_code == 404


@pytest.mark.django_db
def test_item_assign_view_hands_the_item_to_the_chosen_warrior(logged_in_client, current_savegame):
    """
    Flow test: no mocking inside the chain, so this runs the real queue and asserts the end state.
    """
    warrior = WarriorFactory(faction=current_savegame.player_faction)
    item = ItemFactory(savegame=current_savegame, owner=current_savegame.player_faction)

    response = logged_in_client.post(
        reverse("warband:item-assign-view", kwargs={"pk": item.pk}), data={"warrior": warrior.id}
    )

    assert response.status_code == 200
    warrior.refresh_from_db()
    assert warrior.weapon == item


@pytest.mark.django_db
def test_item_assign_view_fills_the_slot_the_item_belongs_in(logged_in_client, current_savegame):
    """
    The slot is the item's own function rather than a URL segment, so there is nothing to get wrong
    and nothing to validate.
    """
    warrior = WarriorFactory(faction=current_savegame.player_faction)
    armor = ItemFactory(
        savegame=current_savegame,
        owner=current_savegame.player_faction,
        type=ItemTypeFactory(function=ItemType.FunctionChoices.FUNCTION_ARMOR),
    )

    logged_in_client.post(reverse("warband:item-assign-view", kwargs={"pk": armor.pk}), data={"warrior": warrior.id})

    warrior.refresh_from_db()
    assert (warrior.armor, warrior.weapon) == (armor, None)


@pytest.mark.django_db
def test_item_assign_view_swaps_with_the_man_already_carrying_it(logged_in_client, current_savegame):
    """
    The card only renders for unused items, but an id can name one somebody holds - and that is a
    swap rather than something to refuse.
    """
    receiver = WarriorFactory(faction=current_savegame.player_faction)
    holder = WarriorFactory(faction=current_savegame.player_faction)
    wanted_item = ItemFactory(savegame=current_savegame, owner=current_savegame.player_faction)
    held_item = ItemFactory(savegame=current_savegame, owner=current_savegame.player_faction)
    receiver.weapon = held_item
    receiver.save()
    holder.weapon = wanted_item
    holder.save()

    logged_in_client.post(
        reverse("warband:item-assign-view", kwargs={"pk": wanted_item.pk}), data={"warrior": receiver.id}
    )

    receiver.refresh_from_db()
    holder.refresh_from_db()
    assert (receiver.weapon, holder.weapon) == (wanted_item, held_item)


@pytest.mark.django_db
def test_item_assign_view_announces_the_changed_lists_to_htmx(logged_in_client, current_savegame):
    warrior = WarriorFactory(faction=current_savegame.player_faction)
    item = ItemFactory(savegame=current_savegame, owner=current_savegame.player_faction)

    response = logged_in_client.post(
        reverse("warband:item-assign-view", kwargs={"pk": item.pk}), data={"warrior": warrior.id}
    )

    assert json.loads(response["HX-Trigger"]) == {"loadFactionItemList": "-", "loadFactionWarriorList": "-"}


@pytest.mark.django_db
def test_item_assign_view_announces_the_far_end_of_a_swap(logged_in_client, current_savegame):
    receiver = WarriorFactory(faction=current_savegame.player_faction)
    holder = WarriorFactory(faction=current_savegame.player_faction)
    wanted_item = ItemFactory(savegame=current_savegame, owner=current_savegame.player_faction)
    holder.weapon = wanted_item
    holder.save()

    response = logged_in_client.post(
        reverse("warband:item-assign-view", kwargs={"pk": wanted_item.pk}), data={"warrior": receiver.id}
    )

    assert "notification" in json.loads(response["HX-Trigger"])


@pytest.mark.django_db
def test_item_assign_view_refuses_a_warrior_off_the_roster(logged_in_client, current_savegame):
    rival_warrior = WarriorFactory(faction=FactionFactory(savegame=current_savegame))
    item = ItemFactory(savegame=current_savegame, owner=current_savegame.player_faction)

    response = logged_in_client.post(
        reverse("warband:item-assign-view", kwargs={"pk": item.pk}), data={"warrior": rival_warrior.id}
    )

    assert response.status_code == 204
    rival_warrior.refresh_from_db()
    assert rival_warrior.weapon is None


@pytest.mark.django_db
def test_item_assign_view_cannot_hand_out_the_item_of_a_rival_faction(logged_in_client, current_savegame):
    """
    Being in the same savegame is not enough - the id from the URL would otherwise be all it takes
    to re-arm a rival's war band for him.
    """
    rival_faction = FactionFactory(savegame=current_savegame)
    rival_warrior = WarriorFactory(faction=rival_faction)
    rival_item = ItemFactory(savegame=current_savegame, owner=rival_faction)

    response = logged_in_client.post(
        reverse("warband:item-assign-view", kwargs={"pk": rival_item.pk}), data={"warrior": rival_warrior.id}
    )

    assert response.status_code == 404
    rival_warrior.refresh_from_db()
    assert rival_warrior.weapon is None


@pytest.mark.django_db
def test_item_assign_view_cannot_hand_out_an_item_of_another_savegame(logged_in_client, current_savegame):
    warrior = WarriorFactory(faction=current_savegame.player_faction)
    other_item = ItemFactory(savegame=SavegameFactory())

    response = logged_in_client.post(
        reverse("warband:item-assign-view", kwargs={"pk": other_item.pk}), data={"warrior": warrior.id}
    )

    assert response.status_code == 404
    warrior.refresh_from_db()
    assert warrior.weapon is None


@pytest.mark.django_db
def test_item_assign_view_without_a_player_faction(logged_in_client, savegame_without_player_faction):
    """
    Nothing belongs to the player yet, so the player-faction scoping narrows to nothing.
    """
    item = ItemFactory(savegame=savegame_without_player_faction)

    response = logged_in_client.post(
        reverse("warband:item-assign-view", kwargs={"pk": item.pk}), data={"warrior": WarriorFactory().id}
    )

    assert response.status_code == 404
