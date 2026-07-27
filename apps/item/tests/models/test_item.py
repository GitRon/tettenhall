import pytest

from apps.item.models.item_type import ItemType
from apps.item.tests.factories.item import ItemFactory
from apps.item.tests.factories.item_type import ItemTypeFactory
from apps.skirmish.tests.factories.warrior import WarriorFactory


@pytest.mark.django_db
def test_is_weapon_for_a_weapon():
    item = ItemFactory(type=ItemTypeFactory(function=ItemType.FunctionChoices.FUNCTION_WEAPON))

    assert item.is_weapon is True


@pytest.mark.django_db
def test_is_armor_for_an_armor():
    item = ItemFactory(type=ItemTypeFactory(function=ItemType.FunctionChoices.FUNCTION_ARMOR))

    assert item.is_armor is True


@pytest.mark.django_db
def test_worn_by_returns_the_wielding_warrior():
    weapon = ItemFactory(type=ItemTypeFactory(function=ItemType.FunctionChoices.FUNCTION_WEAPON))
    warrior = WarriorFactory(weapon=weapon)

    assert weapon.worn_by == warrior


@pytest.mark.django_db
def test_worn_by_returns_the_wearing_warrior():
    armor = ItemFactory(type=ItemTypeFactory(function=ItemType.FunctionChoices.FUNCTION_ARMOR))
    warrior = WarriorFactory(armor=armor)

    assert armor.worn_by == warrior


@pytest.mark.django_db
def test_worn_by_returns_nothing_for_an_unused_item():
    item = ItemFactory(type=ItemTypeFactory(function=ItemType.FunctionChoices.FUNCTION_WEAPON))

    assert item.worn_by is None
