import pytest

from apps.warband.quest.tests.factories.quest import QuestFactory


@pytest.mark.django_db
def test_quest_str():
    quest = QuestFactory(title="A thegn wants hands.")

    assert str(quest) == "A thegn wants hands."
