from unittest import mock

import pytest

from apps.warband.faction.tests.factories.faction import FactionFactory
from apps.warband.quest.tests.factories.quest_contract import QuestContractFactory
from apps.warband.skirmish.models.warrior import Warrior
from apps.warband.skirmish.tests.factories.warrior import WarriorFactory
from apps.warband.training.handlers.commands.training import (
    handle_change_training_regimen,
    handle_progress_warrior_training,
)
from apps.warband.training.messages.commands.training import ChangeTrainingRegimen, TrainWarriors
from apps.warband.training.messages.events.training import TrainingRegimenChanged, WarriorUpgradedSkill
from apps.warband.training.models import Training
from apps.warband.training.tests.factories.training import TrainingFactory


@pytest.mark.django_db
def test_handle_progress_warrior_training_without_a_training():
    """
    A faction owns a training row from NewFactionCreated on, so nothing but a savegame predating that
    reaches this - and the month has to survive it rather than answer with a 500.
    """
    faction = FactionFactory()
    warrior = WarriorFactory(faction=faction, strength=10, strength_progress=40)

    result = handle_progress_warrior_training(context=TrainWarriors(faction=faction, month=6))

    assert result == []
    warrior.refresh_from_db()
    assert warrior.strength_progress == 40


@pytest.mark.django_db
def test_handle_progress_warrior_training_without_healthy_warriors():
    faction = FactionFactory()
    WarriorFactory(faction=faction, condition=Warrior.ConditionChoices.CONDITION_DEAD)
    TrainingFactory(faction=faction, category=Training.TrainingCategory.WEAPON_MASTERY)

    result = handle_progress_warrior_training(context=TrainWarriors(faction=faction, month=6))

    assert result == []


@pytest.mark.django_db
def test_handle_progress_warrior_training_leaves_out_a_man_away_on_last_months_quest():
    """The month on the command is the one beginning; he was away for the one before it."""
    faction = FactionFactory()
    warrior = WarriorFactory(faction=faction, strength=10, strength_progress=40)
    QuestContractFactory(faction=faction, accepted_in_month=5, assigned_warriors=[warrior])
    TrainingFactory(faction=faction, category=Training.TrainingCategory.WEAPON_MASTERY)

    result = handle_progress_warrior_training(context=TrainWarriors(faction=faction, month=6))

    assert result == []
    warrior.refresh_from_db()
    assert warrior.strength_progress == 40


@pytest.mark.django_db
def test_handle_progress_warrior_training_moves_the_bar_on_the_lowest_possible_roll():
    """
    The roll is floored at 1, so there is no month in which a healthy warrior in training gains
    nothing at all. Unfloored, that would happen about one month in six and look like a broken page.
    """
    faction = FactionFactory()
    warrior = WarriorFactory(faction=faction, strength=10, strength_progress=40)
    TrainingFactory(faction=faction, category=Training.TrainingCategory.WEAPON_MASTERY)

    with (
        mock.patch("apps.warband.training.models.training.random.choice", return_value="strength"),
        mock.patch("apps.warband.training.models.training.random.gauss", return_value=-5),
    ):
        result = handle_progress_warrior_training(context=TrainWarriors(faction=faction, month=6))

    assert result == []
    warrior.refresh_from_db()
    assert warrior.strength_progress == 41


@pytest.mark.django_db
def test_handle_progress_warrior_training_fills_progress_bar():
    faction = FactionFactory()
    warrior = WarriorFactory(faction=faction, strength=10, strength_progress=40)
    TrainingFactory(faction=faction, category=Training.TrainingCategory.WEAPON_MASTERY)

    with (
        mock.patch("apps.warband.training.models.training.random.choice", return_value="strength"),
        mock.patch("apps.warband.training.models.training.random.gauss", return_value=30),
    ):
        result = handle_progress_warrior_training(context=TrainWarriors(faction=faction, month=6))

    assert result == []
    warrior.refresh_from_db()
    assert warrior.strength_progress == 70
    assert warrior.strength == 10


@pytest.mark.django_db
def test_handle_progress_warrior_training_upgrades_base_attribute_on_full_progress_bar():
    faction = FactionFactory()
    warrior = WarriorFactory(faction=faction, strength=10, strength_progress=80)
    TrainingFactory(faction=faction, category=Training.TrainingCategory.WEAPON_MASTERY)

    with (
        mock.patch("apps.warband.training.models.training.random.choice", return_value="strength"),
        mock.patch("apps.warband.training.models.training.random.gauss", return_value=30),
    ):
        result = handle_progress_warrior_training(context=TrainWarriors(faction=faction, month=6))

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
    TrainingFactory(faction=faction, category=Training.TrainingCategory.WEAPON_MASTERY)

    with (
        mock.patch("apps.warband.training.models.training.random.choice", return_value="morale"),
        mock.patch("apps.warband.training.models.training.random.gauss", return_value=30),
    ):
        result = handle_progress_warrior_training(context=TrainWarriors(faction=faction, month=6))

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
def test_handle_progress_warrior_training_carries_the_morale_mark_along():
    faction = FactionFactory()
    warrior = WarriorFactory(faction=faction, max_morale=20, morale_progress=80)
    TrainingFactory(faction=faction, category=Training.TrainingCategory.WEAPON_MASTERY)

    with (
        mock.patch("apps.warband.training.models.training.random.choice", return_value="morale"),
        mock.patch("apps.warband.training.models.training.random.gauss", return_value=30),
    ):
        handle_progress_warrior_training(context=TrainWarriors(faction=faction, month=6))

    warrior.refresh_from_db()
    assert warrior.peak_max_morale == 21


@pytest.mark.django_db
def test_handle_progress_warrior_training_leaves_a_mark_the_ceiling_stays_under():
    """
    A man cut from twenty to ten who finishes a course is at eleven, still nine short of what he was.
    """
    faction = FactionFactory()
    warrior = WarriorFactory(faction=faction, max_morale=10, peak_max_morale=20, morale_progress=80)
    TrainingFactory(faction=faction, category=Training.TrainingCategory.WEAPON_MASTERY)

    with (
        mock.patch("apps.warband.training.models.training.random.choice", return_value="morale"),
        mock.patch("apps.warband.training.models.training.random.gauss", return_value=30),
    ):
        handle_progress_warrior_training(context=TrainWarriors(faction=faction, month=6))

    warrior.refresh_from_db()
    assert (warrior.max_morale, warrior.peak_max_morale) == (11, 20)


@pytest.mark.django_db
def test_handle_progress_warrior_training_stores_a_rounded_improvement():
    """
    The progress bar is a positive small integer, so a float improvement would not survive a
    refresh from the database.
    """
    faction = FactionFactory()
    warrior = WarriorFactory(faction=faction, strength=10, strength_progress=40)
    TrainingFactory(faction=faction, category=Training.TrainingCategory.WEAPON_MASTERY)

    with (
        mock.patch("apps.warband.training.models.training.random.choice", return_value="strength"),
        mock.patch("apps.warband.training.models.training.random.gauss", return_value=30.6),
    ):
        handle_progress_warrior_training(context=TrainWarriors(faction=faction, month=6))

    warrior.refresh_from_db()
    assert warrior.strength_progress == 71


@pytest.mark.django_db
def test_handle_progress_warrior_training_advances_faster_in_winter():
    """Month 7 is Winterfylleth, and a winter roll of 20 is worth 30."""
    faction = FactionFactory()
    warrior = WarriorFactory(faction=faction, strength=10, strength_progress=40)
    TrainingFactory(faction=faction, category=Training.TrainingCategory.WEAPON_MASTERY)

    with (
        mock.patch("apps.warband.training.models.training.random.choice", return_value="strength"),
        mock.patch("apps.warband.training.models.training.random.gauss", return_value=20),
    ):
        result = handle_progress_warrior_training(context=TrainWarriors(faction=faction, month=7))

    assert result == []
    warrior.refresh_from_db()
    assert warrior.strength_progress == 70


@pytest.mark.django_db
def test_handle_change_training_regimen_stores_the_new_category():
    training = TrainingFactory(category=Training.TrainingCategory.WEAPON_MASTERY)

    result = handle_change_training_regimen(
        context=ChangeTrainingRegimen(training=training, category=Training.TrainingCategory.SWIFTNESS)
    )

    assert result == TrainingRegimenChanged(training=training)
    training.refresh_from_db()
    assert training.category == Training.TrainingCategory.SWIFTNESS
