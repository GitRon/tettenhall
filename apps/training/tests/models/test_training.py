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
    with pytest.raises(RuntimeError, match="Invalid training category provided."):
        training.get_random_attribute_and_improvement_for_category(category=99)


def test_get_random_attribute_and_improvement_for_category_never_improves_by_less_than_nothing(training):
    with (
        mock.patch("apps.training.models.training.random.choice", return_value="dexterity"),
        mock.patch("apps.training.models.training.random.gauss", return_value=-5),
    ):
        result = training.get_random_attribute_and_improvement_for_category(
            category=Training.TrainingCategory.SWIFTNESS
        )

    assert result == ("dexterity", 0)
