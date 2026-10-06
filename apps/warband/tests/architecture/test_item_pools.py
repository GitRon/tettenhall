import pytest

from apps.warband.item.models.item_type import ItemType
from apps.warband.item.services.generators.item.fyrd import FyrdItemGenerator
from apps.warband.item.services.generators.item.leader import LeaderItemGenerator
from apps.warband.item.services.generators.item.mercenary import MercenaryItemGenerator
from apps.warband.savegame.tests.factories.savegame import SavegameFactory
from apps.warband.town.buildings.weaponsmith import Weaponsmith


@pytest.mark.django_db
@pytest.mark.parametrize("generator_class", (FyrdItemGenerator, LeaderItemGenerator, MercenaryItemGenerator))
@pytest.mark.parametrize(
    "item_function", (ItemType.FunctionChoices.FUNCTION_WEAPON, ItemType.FunctionChoices.FUNCTION_ARMOR)
)
def test_every_pool_holds_something_of_both_functions(generator_class, item_function):
    """
    An empty pool is only ever discovered mid-savegame, as a "No item type found." out of warrior
    generation, so the shipped reference data is asked here instead: every generator has to reach a
    weapon and a piece of armour. A tier renamed or dropped in the fixture then fails in CI.
    """
    generator = generator_class(faction=None, item_function=item_function, savegame_id=SavegameFactory().id)

    result = generator._get_queryset_for_type()

    assert result.exists() is True


@pytest.mark.django_db
@pytest.mark.parametrize("weaponsmith", Weaponsmith.get_levels())
@pytest.mark.parametrize(
    "item_function", (ItemType.FunctionChoices.FUNCTION_WEAPON, ItemType.FunctionChoices.FUNCTION_ARMOR)
)
def test_every_shop_pool_holds_something_of_both_functions(weaponsmith, item_function):
    """
    The same for the town shop, whose bands the weaponsmith sets per level: an empty one would only
    show up at a month's restock.
    """
    generator = MercenaryItemGenerator(
        faction=None,
        item_function=item_function,
        savegame_id=SavegameFactory().id,
        item_tiers=weaponsmith.SHOP_ITEM_TIERS,
    )

    result = generator._get_queryset_for_type()

    assert result.exists() is True
