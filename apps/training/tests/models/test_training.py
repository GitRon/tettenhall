from unittest import mock

import pytest

from apps.training.models import Training
from apps.training.tests.factories.training import TrainingFactory


@pytest.fixture
def training() -> Training:
    return TrainingFactory.build()


def test_get_random_attribute_and_improvement_for_category_weapon_mastery(training):
    # Patched at the boundary: attribute pick and improvement roll are both random
    with (
        mock.patch("apps.training.models.training.random.choice", return_value="strength"),
        mock.patch("apps.training.models.training.random.gauss", return_value=12.4),
    ):
        result = training.get_random_attribute_and_improvement_for_category(
            category=Training.TrainingCategory.WEAPON_MASTERY
        )

    assert result == ("strength", 12)


def test_get_random_attribute_and_improvement_for_category_swiftness(training):
    with (
        mock.patch("apps.training.models.training.random.choice", return_value="dexterity"),
        mock.patch("apps.training.models.training.random.gauss", return_value=12.4),
    ):
        result = training.get_random_attribute_and_improvement_for_category(
            category=Training.TrainingCategory.SWIFTNESS
        )

    assert result == ("dexterity", 12)


def test_get_random_attribute_and_improvement_for_category_shield_wall(training):
    with (
        mock.patch("apps.training.models.training.random.choice", return_value="health"),
        mock.patch("apps.training.models.training.random.gauss", return_value=12.4),
    ):
        result = training.get_random_attribute_and_improvement_for_category(
            category=Training.TrainingCategory.SHIELD_WALL
        )

    assert result == ("health", 12)


def test_get_random_attribute_and_improvement_for_category_unknown_category(training):
    with pytest.raises(RuntimeError, match="Invalid training category provided"):
        training.get_random_attribute_and_improvement_for_category(category=99)


def test_get_random_attribute_and_improvement_for_category_always_improves_by_at_least_one(training):
    """
    A roll below 0.5 rounds to nothing, which at MU 15 / SIGMA 15 is about one month in six. A month of
    training that moves no bar at all reads as a broken page rather than as bad luck, so the floor is 1.
    """
    with (
        mock.patch("apps.training.models.training.random.choice", return_value="dexterity"),
        mock.patch("apps.training.models.training.random.gauss", return_value=-5),
    ):
        result = training.get_random_attribute_and_improvement_for_category(
            category=Training.TrainingCategory.SWIFTNESS
        )

    assert result == ("dexterity", 1)


def test_get_random_attribute_and_improvement_for_category_floors_a_roll_that_rounds_to_zero(training):
    """
    The band the floor exists for: not a negative roll, which "max()" always caught, but the one
    between 0 and 0.5 that rounds down to nothing on the way to an integer column.
    """
    with (
        mock.patch("apps.training.models.training.random.choice", return_value="dexterity"),
        mock.patch("apps.training.models.training.random.gauss", return_value=0.4),
    ):
        result = training.get_random_attribute_and_improvement_for_category(
            category=Training.TrainingCategory.SWIFTNESS
        )

    assert result == ("dexterity", 1)
