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

    with pytest.raises(RuntimeError, match="Invalid difficulty choice."):
        quest.get_min_max_number_of_opponents()


def test_calculate_loot_for_an_easy_quest():
    quest = QuestFactory.build(difficulty=Quest.DifficultyChoices.DIFFICULTY_EASY)

    # Patched at the boundary: the loot roll
    with mock.patch("apps.quest.models.quest.random.randint", return_value=200) as mocked_randint:
        result = quest.calculate_loot()

    assert result == 200
    mocked_randint.assert_called_once_with(150, 350)


def test_calculate_loot_for_a_hard_quest():
    quest = QuestFactory.build(difficulty=Quest.DifficultyChoices.DIFFICULTY_HARD)

    with mock.patch("apps.quest.models.quest.random.randint", return_value=500) as mocked_randint:
        result = quest.calculate_loot()

    assert result == 500
    mocked_randint.assert_called_once_with(250, 750)


def test_calculate_loot_for_an_unknown_difficulty():
    quest = QuestFactory.build(difficulty=99)

    with pytest.raises(RuntimeError, match="Invalid difficulty choice."):
        quest.calculate_loot()
