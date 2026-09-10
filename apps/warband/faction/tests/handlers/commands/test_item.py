from unittest import mock

import pytest

from apps.warband.faction.handlers.commands.item import handle_restock_shop_items
from apps.warband.faction.messages.commands.item import RestockTownShopItems
from apps.warband.faction.messages.events.item import RequestNewItemForTownShop, TownShopRestocked
from apps.warband.faction.tests.factories.faction import FactionFactory
from apps.warband.item.models import ItemType
from apps.warband.item.services.generators.item.mercenary import MercenaryItemGenerator
from apps.warband.item.tests.factories.item import ItemFactory


@pytest.mark.django_db
def test_handle_restock_shop_items_requests_weapons():
    # A Marketplace holds four stalls
    faction = FactionFactory(town__marketplace=1)

    with mock.patch("apps.warband.faction.handlers.commands.item.random.getrandbits", return_value=1):
        result = handle_restock_shop_items(context=RestockTownShopItems(faction=faction, month=3))

    *item_requests, _ = result
    expected_message = RequestNewItemForTownShop(
        faction=faction,
        generator_class=MercenaryItemGenerator,
        item_function=ItemType.FunctionChoices.FUNCTION_WEAPON,
        month=3,
        quality_bonus=0,
    )
    assert item_requests == [expected_message] * 4


@pytest.mark.django_db
def test_handle_restock_shop_items_requests_armor():
    faction = FactionFactory(town__marketplace=1)

    with mock.patch("apps.warband.faction.handlers.commands.item.random.getrandbits", return_value=0):
        result = handle_restock_shop_items(context=RestockTownShopItems(faction=faction, month=3))

    *item_requests, _ = result
    expected_message = RequestNewItemForTownShop(
        faction=faction,
        generator_class=MercenaryItemGenerator,
        item_function=ItemType.FunctionChoices.FUNCTION_ARMOR,
        month=3,
        quality_bonus=0,
    )
    assert item_requests == [expected_message] * 4


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
