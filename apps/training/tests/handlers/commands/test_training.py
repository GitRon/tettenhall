from unittest import mock

import pytest

from apps.faction.tests.factories.faction import FactionFactory
from apps.skirmish.models.warrior import Warrior
from apps.skirmish.tests.factories.warrior import WarriorFactory
from apps.training.handlers.commands.training import handle_progress_warrior_training
from apps.training.messages.commands.training import TrainWarriors
from apps.training.messages.events.training import WarriorUpgradedSkill
from apps.training.models import Training
from apps.training.tests.factories.training import TrainingFactory


@pytest.mark.django_db
def test_handle_progress_warrior_training_without_healthy_warriors():
    faction = FactionFactory()
    WarriorFactory(faction=faction, condition=Warrior.ConditionChoices.CONDITION_DEAD)
    training = TrainingFactory(faction=faction, category=Training.TrainingCategory.WEAPON_MASTERY)

    result = handle_progress_warrior_training(context=TrainWarriors(faction=faction, training=training, month=6))

    assert result == []


@pytest.mark.django_db
def test_handle_progress_warrior_training_moves_the_bar_on_the_lowest_possible_roll():
    """
    The roll is floored at 1, so there is no longer a month in which a healthy warrior in training
    gains nothing at all - which used to happen about one month in six and looked like a broken page.
    """
    faction = FactionFactory()
    warrior = WarriorFactory(faction=faction, strength=10, strength_progress=40)
    training = TrainingFactory(faction=faction, category=Training.TrainingCategory.WEAPON_MASTERY)

    with (
        mock.patch("apps.training.models.training.random.choice", return_value="strength"),
        mock.patch("apps.training.models.training.random.gauss", return_value=-5),
    ):
        result = handle_progress_warrior_training(context=TrainWarriors(faction=faction, training=training, month=6))

    assert result == []
    warrior.refresh_from_db()
    assert warrior.strength_progress == 41


@pytest.mark.django_db
def test_handle_progress_warrior_training_fills_progress_bar():
    faction = FactionFactory()
    warrior = WarriorFactory(faction=faction, strength=10, strength_progress=40)
    training = TrainingFactory(faction=faction, category=Training.TrainingCategory.WEAPON_MASTERY)

    with (
        mock.patch("apps.training.models.training.random.choice", return_value="strength"),
        mock.patch("apps.training.models.training.random.gauss", return_value=30),
    ):
        result = handle_progress_warrior_training(context=TrainWarriors(faction=faction, training=training, month=6))

    assert result == []
    warrior.refresh_from_db()
    assert warrior.strength_progress == 70
    assert warrior.strength == 10


@pytest.mark.django_db
def test_handle_progress_warrior_training_upgrades_base_attribute_on_full_progress_bar():
    faction = FactionFactory()
    warrior = WarriorFactory(faction=faction, strength=10, strength_progress=80)
    training = TrainingFactory(faction=faction, category=Training.TrainingCategory.WEAPON_MASTERY)

    with (
        mock.patch("apps.training.models.training.random.choice", return_value="strength"),
        mock.patch("apps.training.models.training.random.gauss", return_value=30),
    ):
        result = handle_progress_warrior_training(context=TrainWarriors(faction=faction, training=training, month=6))

    assert result == [
        WarriorUpgradedSkill(
            warrior=warrior,
            training_category=Training.TrainingCategory.WEAPON_MASTERY,
            changed_attribute="strength",
            month=6,
        )
    ]
    warrior.refresh_from_db()
    assert warrior.strength == 11
    assert warrior.strength_progress == 0


@pytest.mark.django_db
def test_handle_progress_warrior_training_upgrades_maximum_value_on_full_progress_bar():
    faction = FactionFactory()
    warrior = WarriorFactory(faction=faction, max_morale=20, morale_progress=80)
    training = TrainingFactory(faction=faction, category=Training.TrainingCategory.WEAPON_MASTERY)

    with (
        mock.patch("apps.training.models.training.random.choice", return_value="morale"),
        mock.patch("apps.training.models.training.random.gauss", return_value=30),
    ):
        result = handle_progress_warrior_training(context=TrainWarriors(faction=faction, training=training, month=6))

    assert result == [
        WarriorUpgradedSkill(
            warrior=warrior,
            training_category=Training.TrainingCategory.WEAPON_MASTERY,
            changed_attribute="morale",
            month=6,
        )
    ]
    warrior.refresh_from_db()
    assert warrior.max_morale == 21
    assert warrior.morale_progress == 0


@pytest.mark.django_db
def test_handle_progress_warrior_training_stores_a_rounded_improvement():
    """
    The progress bar is a positive small integer, so a float improvement would not survive a
    refresh from the database.
    """
    faction = FactionFactory()
    warrior = WarriorFactory(faction=faction, strength=10, strength_progress=40)
    training = TrainingFactory(faction=faction, category=Training.TrainingCategory.WEAPON_MASTERY)

    with (
        mock.patch("apps.training.models.training.random.choice", return_value="strength"),
        mock.patch("apps.training.models.training.random.gauss", return_value=30.6),
    ):
        handle_progress_warrior_training(context=TrainWarriors(faction=faction, training=training, month=6))

    warrior.refresh_from_db()
    assert warrior.strength_progress == 71
