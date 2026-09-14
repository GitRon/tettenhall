import pytest

from apps.warband.item.models.item_type import ItemType
from apps.warband.item.services.generators.item.fyrd import FyrdItemGenerator
from apps.warband.savegame.tests.factories.savegame import SavegameFactory


@pytest.mark.django_db
def test_get_queryset_for_type_offers_only_rustic_weapons():
    generator = FyrdItemGenerator(
        faction=None,
        item_function=ItemType.FunctionChoices.FUNCTION_WEAPON,
        savegame_id=SavegameFactory().id,
    )

    result = generator._get_queryset_for_type()

    assert sorted(result.values_list("name", flat=True)) == ["Pitchfork", "Short sword", "Spear"]


@pytest.mark.django_db
def test_get_queryset_for_type_offers_only_rustic_armor():
    """
    A levy off the fields cannot march out in the best mail in the game: the band decides his armour
    the same way it decides his weapon, so Chain mail is out of his reach however the dice fall.
    """
    generator = FyrdItemGenerator(
        faction=None,
        item_function=ItemType.FunctionChoices.FUNCTION_ARMOR,
        savegame_id=SavegameFactory().id,
    )

    result = generator._get_queryset_for_type()

    assert sorted(result.values_list("name", flat=True)) == ["Studded leather"]
