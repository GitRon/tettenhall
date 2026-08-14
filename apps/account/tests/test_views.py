import pytest
from django.urls import reverse

from apps.account.tests.factories.user import UserFactory
from apps.month.tests.factories.player_month_log import PlayerMonthLogFactory
from apps.quest.tests.factories.quest_contract import QuestContractFactory
from apps.savegame.models.savegame import Savegame
from apps.skirmish.tests.factories.skirmish import SkirmishFactory


@pytest.mark.django_db
def test_login_view_sends_an_authenticated_user_to_the_dashboard(logged_in_client):
    response = logged_in_client.get(reverse("account:login-view"))

    assert response.status_code == 302
    assert response.url == reverse("account:dashboard-view")


@pytest.mark.django_db
def test_login_view_authenticates_a_valid_user(client):
    user = UserFactory(email="aethelflaed@mercia.test")
    user.set_password("very-secret")
    user.save()

    response = client.post(
        reverse("account:login-view"), data={"email": "aethelflaed@mercia.test", "password": "very-secret"}
    )

    assert response.status_code == 302
    assert response.url == reverse("account:dashboard-view")
    assert client.session["_auth_user_id"] == str(user.id)


@pytest.mark.django_db
def test_login_view_rejects_a_wrong_password(client):
    """
    Only a single attempt, since django-axes locks the account after three of them.
    """
    user = UserFactory(email="guthrum@danelaw.test")
    user.set_password("very-secret")
    user.save()

    response = client.post(
        reverse("account:login-view"), data={"email": "guthrum@danelaw.test", "password": "wrong-password"}
    )

    assert response.status_code == 200
    assert "_auth_user_id" not in client.session


@pytest.mark.django_db
def test_login_view_locks_the_account_after_three_failed_attempts(client):
    """
    End to end through axes, since AXES_LOCKOUT_TEMPLATE used to point at a template that did not
    exist - so the third attempt raised TemplateDoesNotExist and answered 500.
    """
    user = UserFactory(email="guthrum@danelaw.test")
    user.set_password("very-secret")
    user.save()
    credentials = {"email": "guthrum@danelaw.test", "password": "wrong-password"}

    client.post(reverse("account:login-view"), data=credentials)
    client.post(reverse("account:login-view"), data=credentials)
    response = client.post(reverse("account:login-view"), data=credentials)

    # 429, not 403: that is what AXES_HTTP_RESPONSE_CODE defaults to
    assert response.status_code == 429
    assert "_auth_user_id" not in client.session


@pytest.mark.django_db
def test_login_view_spends_one_attempt_at_a_time_on_an_unknown_email(client):
    """
    The form informed axes on top of LoginView.form_invalid() doing the same, so an unknown email
    spent two of the three allowed failures per attempt and locked out after two tries.
    """
    credentials = {"email": "nobody@tettenhall.test", "password": "wrong-password"}

    client.post(reverse("account:login-view"), data=credentials)
    response = client.post(reverse("account:login-view"), data=credentials)

    assert response.status_code == 200


@pytest.mark.django_db
def test_logout_view_ends_the_session(logged_in_client):
    response = logged_in_client.get(reverse("account:logout-view"))

    assert response.status_code == 302
    assert "_auth_user_id" not in logged_in_client.session


@pytest.mark.django_db
def test_dashboard_view_is_reachable_without_an_active_savegame(logged_in_client):
    """
    Logging in leads straight here, so a user without a savegame sees this page first.
    """
    response = logged_in_client.get(reverse("account:dashboard-view"))

    assert response.status_code == 200


@pytest.mark.django_db
def test_dashboard_view_lists_the_month_logs_of_the_current_savegame(logged_in_client, current_savegame):
    player_month_log = PlayerMonthLogFactory(faction=current_savegame.player_faction)

    response = logged_in_client.get(reverse("account:dashboard-view"))

    assert response.status_code == 200
    assert list(response.context["player_month_logs"]) == [player_month_log]
    assert response.context["faction"] == current_savegame.player_faction


@pytest.mark.django_db
def test_dashboard_view_shows_an_active_quest_with_a_skirmish(logged_in_client, current_savegame):
    skirmish = SkirmishFactory(attacking_faction=current_savegame.player_faction)
    quest_contract = QuestContractFactory(faction=current_savegame.player_faction, skirmish=skirmish)
    current_savegame.player_faction.active_quests.add(quest_contract)

    response = logged_in_client.get(reverse("account:dashboard-view"))

    assert response.status_code == 200


@pytest.mark.django_db
def test_dashboard_view_shows_an_active_quest_without_a_skirmish(logged_in_client, current_savegame):
    """
    QuestContract.skirmish is nullable and cleared on delete, and the template reverses the fight
    url from it - with an empty id that raises NoReverseMatch, so the dashboard answered 500.
    """
    quest_contract = QuestContractFactory(faction=current_savegame.player_faction, skirmish=None)
    current_savegame.player_faction.active_quests.add(quest_contract)

    response = logged_in_client.get(reverse("account:dashboard-view"))

    assert response.status_code == 200


@pytest.mark.django_db
def test_dashboard_view_shows_the_outcome_of_a_finished_savegame(logged_in_client, current_savegame):
    current_savegame.outcome = Savegame.OutcomeChoices.OUTCOME_WON
    current_savegame.save()

    response = logged_in_client.get(reverse("account:dashboard-view"))

    assert response.status_code == 200
    assert response.context["savegame_outcome"] == "Won"
