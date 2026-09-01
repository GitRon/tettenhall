from unittest import mock

import pytest

from apps.common.domain.dice import DiceNotation
from apps.item.models.item import Item
from apps.item.models.item_type import ItemType
from apps.item.services.generators.item.base import BaseItemGenerator
from apps.item.tests.factories.item_type import ItemTypeFactory
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

    with pytest.raises(RuntimeError, match="No item type found"):
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


@pytest.mark.django_db
def test_process_floors_a_modifier_deeper_than_the_die_can_roll():
    """
    A weapon whose modifier undercuts its own best roll cannot deal damage however it is rolled - the
    "Rusty Pitchfork (1d4-4)" a rival turned up with tops out at nothing - and the price does not
    notice, because it clamps the multiplier rather than the modifier.
    """
    # Its own function value, so the queryset cannot draw one of the shipped types instead
    ItemTypeFactory(function=99, base_value="1d4")
    generator = BaseItemGenerator(faction=None, item_function=99, savegame_id=SavegameFactory().id)

    with mock.patch("apps.item.services.generators.item.base.random.gauss", return_value=-20):
        result = generator.process()

    # A 1d4 rolls at best 4, so -3 is as deep as the modifier may go and still leave one point in it
    assert result.modifier == -3
    dice_notation = DiceNotation(dice_string=result.type.base_value, modifier=result.modifier)
    assert dice_notation.best_possible_roll + dice_notation.modifier == 1


@pytest.mark.django_db
def test_process_leaves_a_modifier_the_die_can_still_carry():
    ItemTypeFactory(function=99, base_value="1d4")
    generator = BaseItemGenerator(faction=None, item_function=99, savegame_id=SavegameFactory().id)

    with mock.patch("apps.item.services.generators.item.base.random.gauss", return_value=-2):
        result = generator.process()

    assert result.modifier == -2
