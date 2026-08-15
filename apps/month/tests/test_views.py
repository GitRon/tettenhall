import json

import pytest
from django.urls import reverse

from apps.faction.tests.factories.faction import FactionFactory
from apps.month.models.player_month_log import PlayerMonthLog
from apps.month.tests.factories.player_month_log import PlayerMonthLogFactory
from apps.savegame.models.savegame import Savegame
from apps.savegame.tests.factories.savegame import SavegameFactory
from apps.skirmish.models.warrior import Warrior
from apps.skirmish.tests.factories.skirmish import SkirmishFactory
from apps.skirmish.tests.factories.warrior import WarriorFactory
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
def test_finish_month_view_lets_a_rival_faction_recover(logged_in_client, current_savegame):
    """
    Flow test rather than a unit test on purpose: that the rivals are announced at all only exists in
    the registry, and strict mode's database blocker applies to nothing but a real queue run.

    A warrior knocked unconscious in a battle keeps his condition and his health, and rivals used to
    get no month at all - so a faction that survived one attack stayed crippled for the rest of the
    game and could never be knocked out again. Healing lifts him above zero health, which is what
    turns the condition back to healthy, whatever the sanctuary rolls.
    """
    TrainingFactory(faction=current_savegame.player_faction)
    rival_faction = FactionFactory(savegame=current_savegame)
    rival_warrior = WarriorFactory(
        faction=rival_faction,
        savegame=current_savegame,
        condition=Warrior.ConditionChoices.CONDITION_UNCONSCIOUS,
        current_health=0,
        max_health=20,
    )

    response = logged_in_client.post(reverse("month:finish-month-view"))

    assert response.status_code == 200
    rival_warrior.refresh_from_db()
    assert rival_warrior.condition == Warrior.ConditionChoices.CONDITION_HEALTHY


@pytest.mark.django_db
def test_finish_month_view_logs_the_recovery_of_the_player_faction_only(logged_in_client, current_savegame):
    """
    Flow test rather than a unit test: that the rivals get a month at all only exists in the
    registry, and the producers of these log lines are two handlers away from the one guarding them.

    Both warriors heal - recovery is faction-wide on purpose - but only one of them is bookkeeping
    the player has any business reading. Rival lines used to outnumber his own, a savegame starting
    with three to five of them.
    """
    TrainingFactory(faction=current_savegame.player_faction)
    WarriorFactory(faction=current_savegame.player_faction, current_health=16, max_health=20)
    rival_faction = FactionFactory(savegame=current_savegame)
    WarriorFactory(faction=rival_faction, current_health=18, max_health=20)

    response = logged_in_client.post(reverse("month:finish-month-view"))

    assert response.status_code == 200
    assert PlayerMonthLog.objects.filter(faction=current_savegame.player_faction).exists() is True
    assert PlayerMonthLog.objects.filter(faction=rival_faction).exists() is False


@pytest.mark.django_db
def test_finish_month_view_refuses_a_finished_savegame(logged_in_client, current_savegame):
    """
    Covers the htmx branch of RunningSavegameRequiredMixin; which views carry it at all is asserted
    separately in apps/common/tests/test_ended_savegame_guard.py, and the full-page branch is covered
    by the quest accept view, which is one of the two navigations behind the guard.

    The header is what the browser really sends here - base.html drives this button with "hx-post" -
    and an empty 204 is only the right refusal for a request that can act on one.
    """
    current_savegame.outcome = Savegame.OutcomeChoices.OUTCOME_LOST
    current_savegame.save()

    response = logged_in_client.post(reverse("month:finish-month-view"), headers={"hx-request": "true"})

    assert response.status_code == 204
    assert json.loads(response["HX-Trigger"]) == {"notification": "This game is over. Start a new savegame to play on."}
    current_savegame.refresh_from_db()
    assert current_savegame.current_month == 1


@pytest.mark.django_db
def test_finish_month_view_keeps_the_month_open_while_a_skirmish_is_unresolved(logged_in_client, current_savegame):
    SkirmishFactory(attacking_faction=current_savegame.player_faction)

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
def test_player_month_log_list_view_hides_logs_of_a_rival_faction(logged_in_client, current_savegame):
    """
    Scoping to the savegame is not enough here: the rivals of the player live in it too, and the log
    is his own faction's bookkeeping rather than his savegame's.
    """
    PlayerMonthLogFactory(faction=FactionFactory(savegame=current_savegame))

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
def test_acknowledge_player_month_log_view_cannot_remove_a_log_of_a_rival_faction(logged_in_client, current_savegame):
    """
    The stricter mixin is what closes this one: a rival of the player's own savegame passes the
    savegame scoping, and the id from the URL was enough to acknowledge its row away.
    """
    rival_log = PlayerMonthLogFactory(faction=FactionFactory(savegame=current_savegame))

    response = logged_in_client.delete(reverse("month:player-month-log-remove-view", kwargs={"pk": rival_log.pk}))

    assert response.status_code == 404
    assert PlayerMonthLog.objects.filter(pk=rival_log.pk).exists() is True


@pytest.mark.django_db
def test_finish_month_view_without_an_active_savegame(logged_in_client):
    response = logged_in_client.post(reverse("month:finish-month-view"))

    assert response.status_code == 404
