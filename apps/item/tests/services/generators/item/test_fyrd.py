import pytest

from apps.item.models.item_type import ItemType
from apps.item.services.generators.item.fyrd import FyrdItemGenerator
from apps.savegame.tests.factories.savegame import SavegameFactory


@pytest.mark.django_db
def test_get_queryset_for_type_offers_only_peasant_weapons():
    generator = FyrdItemGenerator(
        faction=None,
        item_function=ItemType.FunctionChoices.FUNCTION_WEAPON,
        savegame_id=SavegameFactory().id,
    )

    result = generator._get_queryset_for_type()

    assert sorted(result.values_list("name", flat=True)) == ["Pitchfork", "Spear"]


@pytest.mark.django_db
def test_get_queryset_for_type_offers_every_armor_but_the_fallback():
    generator = FyrdItemGenerator(
        faction=None,
        item_function=ItemType.FunctionChoices.FUNCTION_ARMOR,
        savegame_id=SavegameFactory().id,
    )

    result = generator._get_queryset_for_type()

    assert sorted(result.values_list("name", flat=True)) == ["Chain mail", "Studded leather"]
