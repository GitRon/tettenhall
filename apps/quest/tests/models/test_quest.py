from unittest import mock

import pytest

from apps.quest.models.quest import Quest
from apps.quest.tests.factories.quest import QuestFactory


def test_str_returns_the_name():
    quest = QuestFactory.build(name="Raid cattle")

    assert str(quest) == "Raid cattle"


def test_get_min_max_number_of_opponents_for_an_easy_quest():
    quest = QuestFactory.build(difficulty=Quest.DifficultyChoices.DIFFICULTY_EASY)

    assert quest.get_min_max_number_of_opponents() == (3, 5)


def test_get_min_max_number_of_opponents_for_a_hard_quest():
    quest = QuestFactory.build(difficulty=Quest.DifficultyChoices.DIFFICULTY_HARD)

    assert quest.get_min_max_number_of_opponents() == (4, 8)


def test_get_min_max_number_of_opponents_for_an_unknown_difficulty():
    quest = QuestFactory.build(difficulty=99)

    with pytest.raises(RuntimeError, match="Invalid difficulty choice"):
        quest.get_min_max_number_of_opponents()


def test_get_min_max_loot_for_an_easy_quest():
    quest = QuestFactory.build(difficulty=Quest.DifficultyChoices.DIFFICULTY_EASY)

    assert quest.get_min_max_loot() == (150, 350)


def test_get_min_max_loot_for_a_hard_quest():
    quest = QuestFactory.build(difficulty=Quest.DifficultyChoices.DIFFICULTY_HARD)

    assert quest.get_min_max_loot() == (250, 750)


def test_get_min_max_loot_for_an_unknown_difficulty():
    quest = QuestFactory.build(difficulty=99)

    with pytest.raises(RuntimeError, match="Invalid difficulty choice"):
        quest.get_min_max_loot()


def test_calculate_loot_for_an_easy_quest():
    quest = QuestFactory.build(difficulty=Quest.DifficultyChoices.DIFFICULTY_EASY, expected_opposition=5)

    # Patched at the boundary: the loot roll
    with mock.patch("apps.quest.models.quest.random.randint", return_value=200) as mocked_randint:
        result = quest.calculate_loot()

    assert result == 200
    mocked_randint.assert_called_once_with(150, 350)


def test_calculate_loot_for_a_hard_quest():
    quest = QuestFactory.build(difficulty=Quest.DifficultyChoices.DIFFICULTY_HARD, expected_opposition=8)

    with mock.patch("apps.quest.models.quest.random.randint", return_value=500) as mocked_randint:
        result = quest.calculate_loot()

    assert result == 500
    mocked_randint.assert_called_once_with(250, 750)


def test_calculate_loot_for_a_target_that_cannot_field_a_full_band():
    """
    A rival opens a savegame with a single warrior, so the top of either band is out of reach for the
    first several months. The contract is written for the war band there is, at a price to match.
    """
    quest = QuestFactory.build(difficulty=Quest.DifficultyChoices.DIFFICULTY_EASY, expected_opposition=1)

    with mock.patch("apps.quest.models.quest.random.randint", return_value=200):
        result = quest.calculate_loot()

    # One man of the five an easy quest is priced for
    assert result == 40


def test_calculate_loot_for_an_unknown_difficulty():
    quest = QuestFactory.build(difficulty=99)

    with pytest.raises(RuntimeError, match="Invalid difficulty choice"):
        quest.calculate_loot()


def test_average_loot_for_an_easy_quest():
    quest = QuestFactory.build(difficulty=Quest.DifficultyChoices.DIFFICULTY_EASY, expected_opposition=5)

    assert quest.average_loot == 250


def test_average_loot_for_a_hard_quest():
    quest = QuestFactory.build(difficulty=Quest.DifficultyChoices.DIFFICULTY_HARD, expected_opposition=8)

    assert quest.average_loot == 500


def test_average_loot_for_a_target_that_cannot_field_a_full_band():
    """
    Scaled the same way the purse is, so the word on the quest card keeps describing the purse: a
    thin contract is not "Low" for being thin, it is mediocre for a contract of its size.
    """
    quest = QuestFactory.build(difficulty=Quest.DifficultyChoices.DIFFICULTY_HARD, expected_opposition=2)

    assert quest.average_loot == 125
