import pytest
from django.urls import reverse

from apps.warband.account.tests.factories.user import UserFactory
from apps.warband.faction.tests.factories.faction import FactionFactory
from apps.warband.month.tests.factories.player_month_log import PlayerMonthLogFactory
from apps.warband.quest.tests.factories.quest_contract import QuestContractFactory
from apps.warband.savegame.models.savegame import Savegame
from apps.warband.skirmish.tests.factories.skirmish import SkirmishFactory
from apps.warband.skirmish.tests.factories.warrior import WarriorFactory
from apps.warband.training.tests.factories.training import TrainingFactory


@pytest.mark.django_db
def test_login_view_sends_an_authenticated_user_to_the_dashboard(logged_in_client):
    response = logged_in_client.get(reverse("warband:login-view"))

    assert response.status_code == 302
    assert response.url == reverse("warband:dashboard-view")


@pytest.mark.django_db
def test_login_view_authenticates_a_valid_user(client):
    user = UserFactory(email="aethelflaed@mercia.test")
    user.set_password("very-secret")
    user.save()

    response = client.post(
        reverse("warband:login-view"), data={"email": "aethelflaed@mercia.test", "password": "very-secret"}
    )

    assert response.status_code == 302
    assert response.url == reverse("warband:dashboard-view")
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
        reverse("warband:login-view"), data={"email": "guthrum@danelaw.test", "password": "wrong-password"}
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

    client.post(reverse("warband:login-view"), data=credentials)
    client.post(reverse("warband:login-view"), data=credentials)
    response = client.post(reverse("warband:login-view"), data=credentials)

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

    client.post(reverse("warband:login-view"), data=credentials)
    response = client.post(reverse("warband:login-view"), data=credentials)

    assert response.status_code == 200


@pytest.mark.django_db
def test_logout_view_ends_the_session(logged_in_client):
    response = logged_in_client.get(reverse("warband:logout-view"))

    assert response.status_code == 302
    assert "_auth_user_id" not in logged_in_client.session


@pytest.mark.django_db
def test_dashboard_view_is_reachable_without_an_active_savegame(logged_in_client):
    """
    Logging in leads straight here, so a user without a savegame sees this page first.
    """
    response = logged_in_client.get(reverse("warband:dashboard-view"))

    assert response.status_code == 200


@pytest.mark.django_db
def test_dashboard_view_lists_the_month_logs_of_the_player_faction(logged_in_client, current_savegame):
    """
    The dashboard is the only place the month log is rendered, and the log is the player faction's -
    scoping to the savegame would put a rival's bookkeeping in front of him.
    """
    player_month_log = PlayerMonthLogFactory(faction=current_savegame.player_faction)
    PlayerMonthLogFactory(faction=FactionFactory(savegame=current_savegame))

    response = logged_in_client.get(reverse("warband:dashboard-view"))

    assert response.status_code == 200
    assert response.context["player_month_logs"].consequence == [player_month_log]
    assert response.context["faction"] == current_savegame.player_faction


@pytest.mark.django_db
def test_dashboard_view_lists_no_month_logs_without_a_player_faction(logged_in_client, savegame_without_player_faction):
    """
    The log is the player faction's, and there is none yet - so there is nothing of his to read.

    The row belongs to a faction of this very savegame, which is what makes the test discriminating:
    scoping to the savegame would list it, scoping to a player faction that does not exist cannot.
    """
    PlayerMonthLogFactory(faction=FactionFactory(savegame=savegame_without_player_faction))

    response = logged_in_client.get(reverse("warband:dashboard-view"))

    assert response.status_code == 200
    assert response.context["player_month_logs"].is_empty is True


@pytest.mark.django_db
def test_dashboard_view_warns_about_a_wage_bill_it_cannot_pay(logged_in_client, current_savegame):
    """
    The warning lives in a branch of the template nothing else renders, and it reverses a url and
    walks two lists inside it - the same shape that answered 500 in the quest case below. A test
    without a shortfall renders none of it.
    """
    WarriorFactory(faction=current_savegame.player_faction, monthly_salary=150, unpaid_months=2)

    response = logged_in_client.get(reverse("warband:dashboard-view"))

    assert response.status_code == 200
    assert response.context["wage_bill_payroll"].is_short is True


@pytest.mark.django_db
def test_dashboard_view_shows_an_active_quest_with_a_skirmish(logged_in_client, current_savegame):
    skirmish = SkirmishFactory(attacking_faction=current_savegame.player_faction)
    quest_contract = QuestContractFactory(faction=current_savegame.player_faction, skirmish=skirmish)
    current_savegame.player_faction.active_quests.add(quest_contract)

    response = logged_in_client.get(reverse("warband:dashboard-view"))

    assert response.status_code == 200


@pytest.mark.django_db
def test_dashboard_view_shows_an_active_quest_without_a_skirmish(logged_in_client, current_savegame):
    """
    QuestContract.skirmish is nullable and cleared on delete, and the template reverses the fight
    url from it - with an empty id that raises NoReverseMatch, so the dashboard answered 500.
    """
    quest_contract = QuestContractFactory(faction=current_savegame.player_faction, skirmish=None)
    current_savegame.player_faction.active_quests.add(quest_contract)

    response = logged_in_client.get(reverse("warband:dashboard-view"))

    assert response.status_code == 200


@pytest.mark.django_db
def test_dashboard_view_shows_the_outcome_of_a_finished_savegame(logged_in_client, current_savegame):
    current_savegame.outcome = Savegame.OutcomeChoices.OUTCOME_WON
    current_savegame.save()

    response = logged_in_client.get(reverse("warband:dashboard-view"))

    assert response.status_code == 200
    assert response.context["savegame_outcome"] == "Won"


@pytest.mark.django_db
def test_dashboard_view_names_the_training_of_the_player_faction(logged_in_client, current_savegame):
    """
    Every faction of the savegame owns a training row, so scoping to the savegame would name
    whichever one happens to come first - a rival's, half the time.
    """
    TrainingFactory(faction=FactionFactory(savegame=current_savegame))
    own_training = TrainingFactory(faction=current_savegame.player_faction)

    response = logged_in_client.get(reverse("warband:dashboard-view"))

    assert response.status_code == 200
    assert response.context["current_training"] == own_training


@pytest.mark.django_db
def test_dashboard_view_names_no_training_without_a_player_faction(logged_in_client, savegame_without_player_faction):
    """
    The lookup needs a faction id, and the template reverses the edit url off whatever it gets - so
    an answer of None is what keeps the page from reversing with an empty id.
    """
    TrainingFactory(faction=FactionFactory(savegame=savegame_without_player_faction))

    response = logged_in_client.get(reverse("warband:dashboard-view"))

    assert response.status_code == 200
    assert response.context["current_training"] is None


@pytest.mark.django_db
def test_dashboard_view_projects_what_is_still_open_this_month(logged_in_client, current_savegame):
    """
    The page the month begins on, so the panels are what it exists to carry. The income key rides
    along because the cost card the dashboard includes reads it.
    """
    response = logged_in_client.get(reverse("warband:dashboard-view"))

    assert response.status_code == 200
    assert response.context["month_standing"].warband.fyrd_reserve == current_savegame.player_faction.fyrd_reserve
    assert response.context["building_income_amount"] == 50


@pytest.mark.django_db
def test_dashboard_view_projects_nothing_once_the_game_is_decided(logged_in_client, current_savegame):
    """
    A decided savegame keeps every control it had, which is #107's to settle - and this page is where
    that would cost the most, since what is still open this month is nothing at all.
    """
    current_savegame.outcome = Savegame.OutcomeChoices.OUTCOME_WON
    current_savegame.save()

    response = logged_in_client.get(reverse("warband:dashboard-view"))

    assert response.status_code == 200
    assert "month_standing" not in response.context


@pytest.mark.django_db
def test_dashboard_view_projects_nothing_without_a_player_faction(logged_in_client, savegame_without_player_faction):
    """
    Every panel is a question about the player's faction, and the savegame row exists before the
    faction does - so the whole assembly answers None rather than each panel guarding separately.
    """
    response = logged_in_client.get(reverse("warband:dashboard-view"))

    assert response.status_code == 200
    assert response.context["month_standing"] is None
