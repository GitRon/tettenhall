from unittest import mock

import pytest

from apps.warband.item.models.item_type import ItemType
from apps.warband.item.services.generators.item.leader import LeaderItemGenerator
from apps.warband.item.services.generators.item.mercenary import MercenaryItemGenerator
from apps.warband.savegame.tests.factories.savegame import SavegameFactory


@pytest.mark.django_db
def test_get_queryset_for_type_offers_weapons_of_both_bands():
    """
    A founding leader is not handed the fine band outright, or the first one killed arms the war band
    better than the forge ever will.
    """
    generator = LeaderItemGenerator(
        faction=None,
        item_function=ItemType.FunctionChoices.FUNCTION_WEAPON,
        savegame_id=SavegameFactory().id,
    )

    result = generator._get_queryset_for_type()

    assert sorted(result.values_list("name", flat=True)) == ["Battle axe", "Pitchfork", "Seax", "Spatha", "Spear"]


@pytest.mark.django_db
def test_get_queryset_for_type_offers_armor_of_both_bands():
    generator = LeaderItemGenerator(
        faction=None,
        item_function=ItemType.FunctionChoices.FUNCTION_ARMOR,
        savegame_id=SavegameFactory().id,
    )

    result = generator._get_queryset_for_type()

    assert sorted(result.values_list("name", flat=True)) == ["Chain mail", "Studded leather"]


@pytest.mark.parametrize(
    "item_function", (ItemType.FunctionChoices.FUNCTION_WEAPON, ItemType.FunctionChoices.FUNCTION_ARMOR)
)
@pytest.mark.django_db
def test_process_rolls_a_mercenarys_mean_at_a_tighter_spread(item_function):
    """
    Well armed, never badly, but not above what a man for hire carries on average: the forge's bonus is
    then the one way past him.
    """
    generator = LeaderItemGenerator(faction=None, item_function=item_function, savegame_id=SavegameFactory().id)
    mercenary = MercenaryItemGenerator(faction=None, item_function=item_function, savegame_id=SavegameFactory().id)

    with mock.patch("apps.warband.item.services.generators.item.base.random.gauss", return_value=0) as mocked_gauss:
        generator.process()

    leader_mu, leader_sigma = mocked_gauss.call_args.args
    mercenary_mu, mercenary_sigma = mercenary._modifier_distribution
    assert leader_mu == mercenary_mu
    assert leader_sigma < mercenary_sigma
