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


@pytest.fixture
def armor_generator(db) -> BaseItemGenerator:
    return BaseItemGenerator(
        faction=None,
        item_function=ItemType.FunctionChoices.FUNCTION_ARMOR,
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


def test_modifier_distribution_for_a_weapon(item_generator):
    result = item_generator._modifier_distribution

    assert result == (BaseItemGenerator.MODIFIER_ROLLS_MU, BaseItemGenerator.MODIFIER_ROLLS_SIGMA)


def test_modifier_distribution_for_armor(armor_generator):
    result = armor_generator._modifier_distribution

    assert result == (BaseItemGenerator.ARMOR_MODIFIER_ROLLS_MU, BaseItemGenerator.ARMOR_MODIFIER_ROLLS_SIGMA)


def test_determine_condition_reads_the_armor_pool(armor_generator):
    """
    The same modifier means two different things on the two functions: three sits inside the weapon
    pool's traditional band and above everything the armour pool has a name for.
    """
    result = armor_generator._determine_condition(modifier=3)

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
def test_process_rolls_armor_from_its_own_pool(armor_generator):
    """
    A mean of its own is the whole point of the split, so the roll has to reach for it rather than for
    the weapon mean sitting on the same class.
    """
    with mock.patch("apps.item.services.generators.item.base.random.gauss", return_value=1) as mocked_gauss:
        result = armor_generator.process()

    assert mocked_gauss.call_args.args == (
        BaseItemGenerator.ARMOR_MODIFIER_ROLLS_MU,
        BaseItemGenerator.ARMOR_MODIFIER_ROLLS_SIGMA,
    )
    assert result.condition == Item.ConditionChoices.CONDITION_TRADITIONAL


@pytest.mark.django_db
def test_process_lifts_armor_by_the_quality_bonus():
    """
    The forge works on mail as well as on blades, and the condition ladder it lifts an item up is the
    armour one - a mean of one plus a bonus of two lands above the armour pool's superior threshold.
    """
    generator = BaseItemGenerator(
        faction=None,
        item_function=ItemType.FunctionChoices.FUNCTION_ARMOR,
        savegame_id=SavegameFactory().id,
        quality_bonus=2,
    )

    with mock.patch("apps.item.services.generators.item.base.random.gauss", return_value=1):
        result = generator.process()

    assert result.modifier == 3
    assert result.condition == Item.ConditionChoices.CONDITION_SUPERIOR


@pytest.mark.django_db
def test_process_floors_an_armor_modifier_deeper_than_the_die_can_roll(armor_generator):
    """
    The floor is reachable on the armour side as well as on the weapon side, and a piece of mail floored
    against its own dice still turns aside a single point. Which armour the generator drew decides how
    deep the floor sits, so the assertion asks the dice rather than naming a number.
    """
    with mock.patch("apps.item.services.generators.item.base.random.gauss", return_value=-20):
        result = armor_generator.process()

    dice_notation = DiceNotation(dice_string=result.type.base_value, modifier=result.modifier)
    assert result.modifier == 1 - dice_notation.best_possible_roll
    assert dice_notation.best_possible_roll + dice_notation.modifier == 1


@pytest.mark.django_db
def test_process_floors_a_modifier_deeper_than_the_die_can_roll():
    """
    A weapon whose modifier undercuts its own best roll cannot deal damage however it is rolled - the
    "Rusty Pitchfork (1d4-4)" a rival turned up with tops out at nothing.
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


@pytest.mark.django_db
def test_process_prices_an_item_by_its_expected_damage():
    """
    The dice decide the damage, so they have to decide the price: a "Cheap Long sword (4d4+0)"
    averaging ten damage is worth more than a "Superior Pitchfork (1d4+5)" averaging seven and a half.
    """
    ItemTypeFactory(function=99, base_value="4d4")
    generator = BaseItemGenerator(faction=None, item_function=99, savegame_id=SavegameFactory().id)

    with mock.patch("apps.item.services.generators.item.base.random.gauss", return_value=0):
        result = generator.process()

    assert result.price == 100


@pytest.mark.django_db
def test_process_prices_an_item_that_barely_threatens_anybody_at_the_floor():
    """
    A modifier floored against a small die leaves an expectancy below a single point of damage, which
    is not a price - the item is worth the floor instead.
    """
    ItemTypeFactory(function=99, base_value="1d4")
    generator = BaseItemGenerator(faction=None, item_function=99, savegame_id=SavegameFactory().id)

    # A 1d4 floors the modifier at -3, leaving an expectancy of -0.5
    with mock.patch("apps.item.services.generators.item.base.random.gauss", return_value=-20):
        result = generator.process()

    assert result.price == 10
