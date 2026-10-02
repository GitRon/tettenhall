import pytest
from django.contrib.messages import get_messages
from django.urls import reverse

from apps.warband.quest.models.quest import Quest
from apps.warband.quest.models.quest_contract import QuestContract
from apps.warband.quest.tests.factories.quest import QuestFactory
from apps.warband.savegame.models.savegame import Savegame
from apps.warband.skirmish.tests.factories.warrior import WarriorFactory


@pytest.mark.django_db
def test_quest_accept_view_sends_the_men(logged_in_client, current_savegame):
    """
    Flow test: no mocking inside the chain, so this runs the real queue and asserts the end state.
    """
    quest = QuestFactory(faction=current_savegame.player_faction, month=current_savegame.current_month)
    warrior = WarriorFactory(faction=current_savegame.player_faction)

    response = logged_in_client.post(
        reverse("warband:quest-accept-view", kwargs={"pk": quest.pk}), data={"assigned_warriors": [warrior.id]}
    )

    assert response.status_code == 302
    assert response.url == reverse("warband:town-board-view")
    assert [str(message) for message in get_messages(response.wsgi_request)] == [f"Your men set out: {quest}"]
    assert list(QuestContract.objects.get(faction=current_savegame.player_faction).assigned_warriors.all()) == [warrior]
    assert Quest.objects.filter(pk=quest.pk).exists() is False


@pytest.mark.django_db
def test_quest_accept_view_shows_the_quest(logged_in_client, current_savegame):
    quest = QuestFactory(faction=current_savegame.player_faction, month=current_savegame.current_month)

    response = logged_in_client.get(reverse("warband:quest-accept-view", kwargs={"pk": quest.pk}))

    assert response.status_code == 200
    assert response.context["object"] == quest


@pytest.mark.django_db
def test_quest_accept_view_redisplays_the_quest_on_an_invalid_submission(logged_in_client, current_savegame):
    quest = QuestFactory(faction=current_savegame.player_faction, month=current_savegame.current_month)

    response = logged_in_client.post(reverse("warband:quest-accept-view", kwargs={"pk": quest.pk}), data={})

    assert response.status_code == 200
    assert QuestContract.objects.exists() is False


@pytest.mark.django_db
def test_quest_accept_view_refuses_last_months_offer(logged_in_client, current_savegame):
    """A stale tab: the board the offer was on has been redrawn since."""
    current_savegame.current_month = 3
    current_savegame.save()
    quest = QuestFactory(faction=current_savegame.player_faction, month=2)
    warrior = WarriorFactory(faction=current_savegame.player_faction)

    response = logged_in_client.post(
        reverse("warband:quest-accept-view", kwargs={"pk": quest.pk}), data={"assigned_warriors": [warrior.id]}
    )

    assert response.status_code == 404
    assert QuestContract.objects.exists() is False


@pytest.mark.django_db
def test_quest_accept_view_refuses_a_rivals_offer(logged_in_client, current_savegame):
    quest = QuestFactory(faction__savegame=current_savegame, month=current_savegame.current_month)
    warrior = WarriorFactory(faction=current_savegame.player_faction)

    response = logged_in_client.post(
        reverse("warband:quest-accept-view", kwargs={"pk": quest.pk}), data={"assigned_warriors": [warrior.id]}
    )

    assert response.status_code == 404
    assert QuestContract.objects.exists() is False


@pytest.mark.django_db
def test_quest_accept_view_without_a_player_faction(logged_in_client, savegame_without_player_faction):
    quest = QuestFactory(faction__savegame=savegame_without_player_faction)

    response = logged_in_client.post(reverse("warband:quest-accept-view", kwargs={"pk": quest.pk}), data={})

    assert response.status_code == 404


@pytest.mark.django_db
def test_quest_accept_view_without_a_savegame(logged_in_client):
    quest = QuestFactory()

    response = logged_in_client.get(reverse("warband:quest-accept-view", kwargs={"pk": quest.pk}))

    assert response.status_code == 404


@pytest.mark.django_db
def test_quest_accept_view_sends_the_player_home_on_a_finished_savegame(logged_in_client, current_savegame):
    """
    The full-page branch of RunningSavegameRequiredMixin. A browser handed a 204 for a plain
    navigation abandons it without a word, so the refusal is a redirect the player can see.
    """
    quest = QuestFactory(faction=current_savegame.player_faction, month=current_savegame.current_month)
    current_savegame.outcome = Savegame.OutcomeChoices.OUTCOME_LOST
    current_savegame.save()

    response = logged_in_client.get(reverse("warband:quest-accept-view", kwargs={"pk": quest.pk}))

    assert response.status_code == 302
    assert response.url == reverse("warband:dashboard-view")


@pytest.mark.django_db
def test_quest_accept_view_tells_a_finished_savegame_so_even_for_a_stale_offer(logged_in_client, current_savegame):
    """
    An offer from an earlier month is no longer found, and a game that is over has to say that it is
    over rather than that the offer does not exist.
    """
    quest = QuestFactory(faction=current_savegame.player_faction, month=current_savegame.current_month - 1)
    current_savegame.outcome = Savegame.OutcomeChoices.OUTCOME_LOST
    current_savegame.save()

    response = logged_in_client.get(reverse("warband:quest-accept-view", kwargs={"pk": quest.pk}))

    assert response.status_code == 302
    assert response.url == reverse("warband:dashboard-view")
