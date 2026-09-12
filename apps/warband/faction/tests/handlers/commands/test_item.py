from collections import Counter
from unittest import mock

import pytest

from apps.warband.faction.handlers.commands.item import (
    handle_add_item_to_shop,
    handle_buy_item_for_faction,
    handle_restock_shop_items,
)
from apps.warband.faction.messages.commands.item import (
    AddItemToTownShop,
    RemoveItemFromTownShop,
    RestockTownShopItems,
)
from apps.warband.faction.messages.events.item import (
    ItemWasAddedToShop,
    ItemWasRemovedFromShop,
    TownShopRestocked,
)
from apps.warband.faction.tests.factories.faction import FactionFactory
from apps.warband.item.models import ItemType
from apps.warband.item.services.generators.item.mercenary import MercenaryItemGenerator
from apps.warband.item.tests.factories.item import ItemFactory


@pytest.mark.django_db
def test_handle_restock_shop_items_requests_a_weapon_even_when_every_flip_says_armor():
    """
    A month of nothing but armour is a month the shop offers the player no decision, and three
    independent flips reach it once in eight.
    """
    # A Marketplace holds four stalls
    faction = FactionFactory(town__marketplace=1)

    with mock.patch("apps.warband.faction.handlers.commands.item.random.getrandbits", return_value=0):
        result = handle_restock_shop_items(context=RestockTownShopItems(faction=faction, month=3))

    *item_requests, _ = result
    assert Counter(message.item_function for message in item_requests) == Counter(
        {ItemType.FunctionChoices.FUNCTION_ARMOR: 3, ItemType.FunctionChoices.FUNCTION_WEAPON: 1}
    )


@pytest.mark.django_db
def test_handle_restock_shop_items_requests_an_armor_even_when_every_flip_says_weapon():
    faction = FactionFactory(town__marketplace=1)

    with mock.patch("apps.warband.faction.handlers.commands.item.random.getrandbits", return_value=1):
        result = handle_restock_shop_items(context=RestockTownShopItems(faction=faction, month=3))

    *item_requests, _ = result
    assert Counter(message.item_function for message in item_requests) == Counter(
        {ItemType.FunctionChoices.FUNCTION_WEAPON: 3, ItemType.FunctionChoices.FUNCTION_ARMOR: 1}
    )


@pytest.mark.django_db
def test_handle_restock_shop_items_keeps_both_kinds_in_the_smallest_market():
    """
    Level 0 is where a savegame opens and the guarantee has the least room: two of its three stalls
    are spoken for, and only the third is flipped for.
    """
    faction = FactionFactory(town__marketplace=0)

    with mock.patch("apps.warband.faction.handlers.commands.item.random.getrandbits", return_value=1):
        result = handle_restock_shop_items(context=RestockTownShopItems(faction=faction, month=3))

    *item_requests, _ = result
    assert Counter(message.item_function for message in item_requests) == Counter(
        {ItemType.FunctionChoices.FUNCTION_WEAPON: 2, ItemType.FunctionChoices.FUNCTION_ARMOR: 1}
    )


@pytest.mark.django_db
def test_handle_restock_shop_items_asks_the_mercenary_generator_for_every_stall():
    """
    The shop stocks what a professional would carry whatever the town is, so the archetype is the
    one thing about a stall that is not drawn.
    """
    faction = FactionFactory(town__marketplace=1)

    result = handle_restock_shop_items(context=RestockTownShopItems(faction=faction, month=3))

    *item_requests, _ = result
    assert {message.generator_class for message in item_requests} == {MercenaryItemGenerator}


@pytest.mark.django_db
def test_handle_restock_shop_items_stocks_as_many_items_as_the_market_has_stalls():
    """
    The stock size used to be a dice roll between four and five, so no building had a say in it.
    """
    faction = FactionFactory(town__marketplace=3)

    result = handle_restock_shop_items(context=RestockTownShopItems(faction=faction, month=3))

    *item_requests, _ = result
    # A High Market holds eight, against the three a town without a market manages
    assert len(item_requests) == 8


@pytest.mark.django_db
def test_handle_restock_shop_items_passes_the_quality_of_the_weaponsmith():
    faction = FactionFactory(town__weaponsmith=3)

    result = handle_restock_shop_items(context=RestockTownShopItems(faction=faction, month=3))

    *item_requests, _ = result
    # A Master Forge adds three to every modifier roll in the shop
    assert {message.quality_bonus for message in item_requests} == {3}


@pytest.mark.django_db
def test_handle_restock_shop_items_announces_the_whole_shop_once():
    faction = FactionFactory(town__marketplace=1)

    result = handle_restock_shop_items(context=RestockTownShopItems(faction=faction, month=3))

    assert result[-1] == TownShopRestocked(faction=faction, new_items=4, month=3)


@pytest.mark.django_db
def test_handle_restock_shop_items_removes_previous_stock():
    faction = FactionFactory()
    faction.available_items.add(ItemFactory())

    with (
        mock.patch("apps.warband.faction.handlers.commands.item.random.randrange", return_value=4),
        mock.patch("apps.warband.faction.handlers.commands.item.random.getrandbits", return_value=1),
    ):
        handle_restock_shop_items(context=RestockTownShopItems(faction=faction, month=3))

    assert faction.available_items.count() == 0


@pytest.mark.django_db
def test_handle_add_item_to_shop_puts_the_item_on_the_shelf():
    faction = FactionFactory()
    item = ItemFactory()

    result = handle_add_item_to_shop(context=AddItemToTownShop(faction=faction, item=item, month=3))

    assert result == ItemWasAddedToShop(faction=faction, item=item, month=3)
    assert list(faction.available_items.all()) == [item]


@pytest.mark.django_db
def test_handle_add_item_to_shop_leaves_the_owner_to_the_item_package():
    """
    Stocking the shelf is a membership change and nothing else, so an owner the item arrives with
    survives it. Ownership is settled through Item.objects.update_ownership() before this command is
    ever dispatched.
    """
    faction = FactionFactory()
    item = ItemFactory(owner=faction)

    handle_add_item_to_shop(context=AddItemToTownShop(faction=faction, item=item, month=3))

    item.refresh_from_db()
    assert item.owner == faction


@pytest.mark.django_db
def test_handle_buy_item_for_faction_takes_the_item_off_the_shelf():
    faction = FactionFactory()
    item = ItemFactory()
    faction.available_items.add(item)

    result = handle_buy_item_for_faction(context=RemoveItemFromTownShop(faction=faction, item=item, month=3))

    assert result == ItemWasRemovedFromShop(faction=faction, item=item, month=3)
    assert faction.available_items.count() == 0


@pytest.mark.django_db
def test_handle_buy_item_for_faction_leaves_the_owner_to_the_item_package():
    """
    The buyer is written by the SellItem/BuyItem pair in the "item" package, so clearing the shelf
    does not hand the item over a second time.
    """
    faction = FactionFactory()
    item = ItemFactory()
    faction.available_items.add(item)

    handle_buy_item_for_faction(context=RemoveItemFromTownShop(faction=faction, item=item, month=3))

    item.refresh_from_db()
    assert item.owner is None
