import pytest

from apps.warband.quest.models.quest import Quest
from apps.warband.quest.tests.factories.quest import QuestFactory


@pytest.mark.django_db
def test_for_player_faction():
    quest = QuestFactory()
    QuestFactory()

    assert list(Quest.objects.for_player_faction(faction_id=quest.faction_id)) == [quest]


@pytest.mark.django_db
def test_offered_in():
    quest = QuestFactory(month=3)
    QuestFactory(faction=quest.faction, month=2)

    assert list(Quest.objects.offered_in(month=3)) == [quest]
