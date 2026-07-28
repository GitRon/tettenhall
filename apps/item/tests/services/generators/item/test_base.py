from unittest import mock

import pytest

from apps.item.models.item import Item
from apps.item.models.item_type import ItemType
from apps.item.services.generators.item.base import BaseItemGenerator
from apps.savegame.tests.factories.savegame import SavegameFactory


@pytest.fixture
def item_generator(db) -> BaseItemGenerator:
    return BaseItemGenerator(
        faction=None,
        item_function=ItemType.FunctionChoices.FUNCTION_WEAPON,
        savegame_id=SavegameFactory().id,
    )


def test_determine_condition_below_the_expected_range(item_generator):
    result = item_generator._determine_condition(modifier=-1)

    assert result == Item.ConditionChoices.CONDITION_RUSTY


def test_determine_condition_within_one_sigma_below_the_mean(item_generator):
    result = item_generator._determine_condition(modifier=1)

    assert result == Item.ConditionChoices.CONDITION_CHEAP


def test_determine_condition_within_one_sigma_above_the_mean(item_generator):
    result = item_generator._determine_condition(modifier=3)

    assert result == Item.ConditionChoices.CONDITION_TRADITIONAL


def test_determine_condition_above_the_expected_range(item_generator):
    result = item_generator._determine_condition(modifier=4)

    assert result == Item.ConditionChoices.CONDITION_SUPERIOR


@pytest.mark.django_db
def test_process_without_a_matching_item_type():
    generator = BaseItemGenerator(faction=None, item_function=99, savegame_id=SavegameFactory().id)

    with pytest.raises(RuntimeError, match="No item type found."):
        generator.process()


@pytest.mark.django_db
def test_process_lifts_the_item_by_the_quality_bonus():
    """
    The condition thresholds sit on the generator's own mean, so the bonus has to be added to the
    roll rather than raising that mean - raising it would move the thresholds along with it and
    leave the condition distribution exactly as it was.
    """
    generator = BaseItemGenerator(
        faction=None,
        item_function=ItemType.FunctionChoices.FUNCTION_WEAPON,
        savegame_id=SavegameFactory().id,
        quality_bonus=3,
    )

    # Rolling the mean of 2 plus the bonus of 3 lands above the superior threshold of 4
    with mock.patch("apps.item.services.generators.item.base.random.gauss", return_value=2):
        result = generator.process()

    assert result.modifier == 5
    assert result.condition == Item.ConditionChoices.CONDITION_SUPERIOR


@pytest.mark.django_db
def test_process_without_a_quality_bonus():
    generator = BaseItemGenerator(
        faction=None,
        item_function=ItemType.FunctionChoices.FUNCTION_WEAPON,
        savegame_id=SavegameFactory().id,
    )

    with mock.patch("apps.item.services.generators.item.base.random.gauss", return_value=2):
        result = generator.process()

    assert result.modifier == 2
    assert result.condition == Item.ConditionChoices.CONDITION_TRADITIONAL
