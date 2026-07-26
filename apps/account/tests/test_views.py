import pytest
from django.urls import reverse

from apps.account.tests.factories.user import UserFactory
from apps.month.tests.factories.player_month_log import PlayerMonthLogFactory


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
