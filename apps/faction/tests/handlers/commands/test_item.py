import pytest

from apps.faction.handlers.commands.item import (
    handle_add_item_to_shop,
    handle_buy_item_for_faction,
    handle_sell_item_from_faction,
)
from apps.faction.messages.commands.item import AddItemToTownShop, RemoveItemFromTownShop
from apps.faction.messages.events.item import ItemWasAddedToShop, ItemWasRemovedFromShop
from apps.faction.tests.factories.faction import FactionFactory
from apps.item.tests.factories.item import ItemFactory


@pytest.fixture
def faction(db):
    return FactionFactory()


@pytest.fixture
def item(db):
    return ItemFactory()


@pytest.fixture
def month():
    return 1


def test_handle_add_item_to_shop(faction, item, month):
    # Arrange
    context = AddItemToTownShop(faction=faction, item=item, month=month)

    # Act
    result = handle_add_item_to_shop(context=context)

    # Assert
    assert item in faction.available_items.all()
    assert isinstance(result, ItemWasAddedToShop)
    assert result.faction == faction
    assert result.item == item
    assert result.month == month


def test_handle_buy_item_for_faction(faction, item, month):
    # Arrange
    faction.available_items.add(item)
    context = RemoveItemFromTownShop(faction=faction, item=item, month=month)

    # Act
    result = handle_buy_item_for_faction(context=context)

    # Assert
    item.refresh_from_db()
    assert item.owner == faction
    assert item not in faction.available_items.all()
    assert isinstance(result, ItemWasRemovedFromShop)
    assert result.faction == faction
    assert result.item == item
    assert result.month == month


def test_handle_sell_item_from_faction(faction, item, month):
    # Arrange
    # Set initial owner to faction
    item.owner = faction
    item.save()
    context = AddItemToTownShop(faction=faction, item=item, month=month)

    # Act
    result = handle_sell_item_from_faction(context=context)

    # Assert
    item.refresh_from_db()
    assert item.owner is None
    assert item in faction.available_items.all()
    assert isinstance(result, ItemWasAddedToShop)
    assert result.faction == faction
    assert result.item == item
    assert result.month == month


def test_handle_add_item_to_shop_already_in_shop(faction, item, month):
    """Test adding an item that's already in the shop."""
    # Arrange
    # Add the item to the shop first
    faction.available_items.add(item)
    context = AddItemToTownShop(faction=faction, item=item, month=month)

    # Act
    result = handle_add_item_to_shop(context=context)

    # Assert
    assert item in faction.available_items.all()
    assert isinstance(result, ItemWasAddedToShop)
    assert result.faction == faction
    assert result.item == item
    assert result.month == month


def test_handle_buy_item_for_faction_not_in_shop(faction, item, month):
    """Test buying an item that's not in the shop."""
    # Arrange
    # Don't add the item to the shop
    context = RemoveItemFromTownShop(faction=faction, item=item, month=month)

    # Act & Assert
    with pytest.raises(
        Exception
    ):  # Django will raise an exception when trying to remove an item that's not in the shop
        handle_buy_item_for_faction(context=context)

    # Verify that the item's owner was set before the exception was raised
    item.refresh_from_db()
    assert item.owner == faction


def test_handle_sell_item_from_faction_not_owned(faction, item, month):
    """Test selling an item that's not owned by the faction."""
    # Arrange
    # Set the item's owner to None to simulate that it's not owned by the faction
    item.owner = None
    item.save()
    context = AddItemToTownShop(faction=faction, item=item, month=month)

    # Act
    result = handle_sell_item_from_faction(context=context)

    # Assert
    # The owner should still be None
    item.refresh_from_db()
    assert item.owner is None
    assert item in faction.available_items.all()
    assert isinstance(result, ItemWasAddedToShop)
    assert result.faction == faction
    assert result.item == item
    assert result.month == month
