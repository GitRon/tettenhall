import pytest

from apps.warband.item.models.item_type import ItemType
from apps.warband.item.services.generators.item.leader import LeaderItemGenerator
from apps.warband.savegame.tests.factories.savegame import SavegameFactory


@pytest.mark.django_db
def test_get_queryset_for_type_offers_only_fine_weapons():
    generator = LeaderItemGenerator(
        faction=None,
        item_function=ItemType.FunctionChoices.FUNCTION_WEAPON,
        savegame_id=SavegameFactory().id,
    )

    result = generator._get_queryset_for_type()

    assert sorted(result.values_list("name", flat=True)) == ["Battle axe", "Long sword"]


@pytest.mark.django_db
def test_get_queryset_for_type_offers_only_fine_armor():
    generator = LeaderItemGenerator(
        faction=None,
        item_function=ItemType.FunctionChoices.FUNCTION_ARMOR,
        savegame_id=SavegameFactory().id,
    )

    result = generator._get_queryset_for_type()

    assert sorted(result.values_list("name", flat=True)) == ["Chain mail"]
