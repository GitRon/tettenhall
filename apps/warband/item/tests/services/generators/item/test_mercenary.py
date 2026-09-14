import pytest

from apps.warband.item.models.item_type import ItemType
from apps.warband.item.services.generators.item.mercenary import MercenaryItemGenerator
from apps.warband.savegame.tests.factories.savegame import SavegameFactory


@pytest.mark.django_db
def test_get_queryset_for_type_offers_every_weapon_but_the_fallback():
    """
    Both bands is the whole table, and the town shop draws its wares through this generator - a man for
    hire and a market stall are the two places every weapon in the game is reachable from.
    """
    generator = MercenaryItemGenerator(
        faction=None,
        item_function=ItemType.FunctionChoices.FUNCTION_WEAPON,
        savegame_id=SavegameFactory().id,
    )

    result = generator._get_queryset_for_type()

    assert sorted(result.values_list("name", flat=True)) == [
        "Battle axe",
        "Long sword",
        "Pitchfork",
        "Short sword",
        "Spear",
    ]


@pytest.mark.django_db
def test_get_queryset_for_type_offers_every_armor_but_the_fallback():
    generator = MercenaryItemGenerator(
        faction=None,
        item_function=ItemType.FunctionChoices.FUNCTION_ARMOR,
        savegame_id=SavegameFactory().id,
    )

    result = generator._get_queryset_for_type()

    assert sorted(result.values_list("name", flat=True)) == ["Chain mail", "Studded leather"]
