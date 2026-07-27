import pytest

from apps.item.models.item_type import ItemType
from apps.item.tests.factories.item_type import ItemTypeFactory


@pytest.mark.django_db
def test_str_contains_name_and_function():
    item_type = ItemTypeFactory(name="Battle axe", function=ItemType.FunctionChoices.FUNCTION_WEAPON)

    assert str(item_type) == "Battle axe (Weapon)"
