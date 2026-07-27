import json

import pytest
from django.urls import reverse

from apps.faction.tests.factories.faction import FactionFactory
from apps.month.models.player_month_log import PlayerMonthLog
from apps.month.tests.factories.player_month_log import PlayerMonthLogFactory
from apps.savegame.tests.factories.savegame import SavegameFactory
from apps.skirmish.tests.factories.skirmish import SkirmishFactory
from apps.training.tests.factories.training import TrainingFactory


@pytest.mark.django_db
def test_finish_month_view_advances_the_savegame_to_the_next_month(logged_in_client, current_savegame):
    """
    Flow test: no mocking inside the chain, so this runs the real month change and asserts the end state.

    The chain trains the warriors of the current training and restocks the bulletin board, so the
    savegame needs a training and a faction to send the player against.
    """
    TrainingFactory(faction=current_savegame.player_faction)
    FactionFactory(savegame=current_savegame)

    response = logged_in_client.post(reverse("month:finish-month-view"))

    assert response.status_code == 200
    assert response["HX-Redirect"] == reverse("account:dashboard-view")
    current_savegame.refresh_from_db()
    assert current_savegame.current_month == 2


@pytest.mark.django_db
def test_finish_month_view_keeps_the_month_open_while_a_skirmish_is_unresolved(logged_in_client, current_savegame):
    SkirmishFactory(player_faction=current_savegame.player_faction)

    response = logged_in_client.post(reverse("month:finish-month-view"))

    assert response.status_code == 204
    assert json.loads(response["HX-Trigger"]) == {
        "notification": "Please resolve all open skirmishes before you finish this month."
    }
    current_savegame.refresh_from_db()
    assert current_savegame.current_month == 1


@pytest.mark.django_db
def test_player_month_log_list_view_lists_the_logs_of_the_player_faction(logged_in_client, current_savegame):
    player_month_log = PlayerMonthLogFactory(faction=current_savegame.player_faction)

    response = logged_in_client.get(reverse("month:player-month-log-list-view"))

    assert response.status_code == 200
    assert list(response.context["playermonthlog_list"]) == [player_month_log]


@pytest.mark.django_db
def test_player_month_log_list_view_hides_logs_of_another_savegame(logged_in_client, current_savegame):
    other_savegame = SavegameFactory()
    PlayerMonthLogFactory(faction__savegame=other_savegame)

    response = logged_in_client.get(reverse("month:player-month-log-list-view"))

    assert response.status_code == 200
    assert list(response.context["playermonthlog_list"]) == []


@pytest.mark.django_db
def test_acknowledge_player_month_log_view_removes_the_log(logged_in_client, current_savegame):
    player_month_log = PlayerMonthLogFactory(faction=current_savegame.player_faction)

    response = logged_in_client.delete(
        reverse("month:player-month-log-remove-view", kwargs={"pk": player_month_log.pk})
    )

    assert response.status_code == 202
    assert json.loads(response["HX-Trigger"]) == {"loadMessageList": "-"}
    assert PlayerMonthLog.objects.filter(pk=player_month_log.pk).exists() is False


@pytest.mark.django_db
def test_acknowledge_player_month_log_view_cannot_remove_a_log_of_another_savegame(logged_in_client, current_savegame):
    """
    Without the savegame scoping the id from the URL would be enough to drop another player's message.
    """
    other_savegame = SavegameFactory()
    foreign_log = PlayerMonthLogFactory(faction__savegame=other_savegame)

    response = logged_in_client.delete(reverse("month:player-month-log-remove-view", kwargs={"pk": foreign_log.pk}))

    assert response.status_code == 404
    assert PlayerMonthLog.objects.filter(pk=foreign_log.pk).exists() is True


@pytest.mark.django_db
def test_finish_month_view_without_an_active_savegame(logged_in_client):
    response = logged_in_client.post(reverse("month:finish-month-view"))

    assert response.status_code == 404
