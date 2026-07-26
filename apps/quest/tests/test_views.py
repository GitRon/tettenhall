import pytest
from django.urls import reverse

from apps.quest.models.quest_contract import QuestContract
from apps.quest.tests.factories.quest import QuestFactory
from apps.savegame.tests.factories.savegame import SavegameFactory
from apps.skirmish.tests.factories.warrior import WarriorFactory


@pytest.mark.django_db
def test_quest_accept_view_signs_a_contract_and_sets_up_the_skirmish(logged_in_client, current_savegame):
    """
    Flow test: no mocking inside the chain, so this runs the real queue and asserts the end state.
    """
    quest = QuestFactory(target_faction__savegame=current_savegame)
    warrior = WarriorFactory(faction=current_savegame.player_faction)
    current_savegame.player_faction.available_quests.add(quest)

    response = logged_in_client.post(
        reverse("quest:quest-accept-view", kwargs={"pk": quest.pk}),
        data={
            "faction": current_savegame.player_faction.id,
            "quest": quest.id,
            "assigned_warriors": [warrior.id],
        },
    )

    assert response.status_code == 302
    assert "HX-Trigger" in response.headers
    quest_contract = QuestContract.objects.get(quest=quest, faction=current_savegame.player_faction)
    assert list(quest_contract.assigned_warriors.all()) == [warrior]
    assert quest_contract.skirmish is not None


@pytest.mark.django_db
def test_quest_accept_view_redisplays_the_quest_on_an_invalid_submission(logged_in_client, current_savegame):
    quest = QuestFactory(target_faction__savegame=current_savegame)

    response = logged_in_client.post(reverse("quest:quest-accept-view", kwargs={"pk": quest.pk}), data={})

    assert response.status_code == 200
    assert response.context["object"] == quest
    assert QuestContract.objects.exists() is False


@pytest.mark.django_db
def test_quest_accept_view_cannot_accept_a_quest_of_another_savegame(logged_in_client, current_savegame):
    """
    Without the savegame scoping the id from the URL would be enough to accept another player's quest.
    """
    other_savegame = SavegameFactory()
    foreign_quest = QuestFactory(target_faction__savegame=other_savegame)
    warrior = WarriorFactory(faction=current_savegame.player_faction)

    response = logged_in_client.post(
        reverse("quest:quest-accept-view", kwargs={"pk": foreign_quest.pk}),
        data={
            "faction": current_savegame.player_faction.id,
            "quest": foreign_quest.id,
            "assigned_warriors": [warrior.id],
        },
    )

    assert response.status_code == 404
    assert QuestContract.objects.filter(quest=foreign_quest).exists() is False
