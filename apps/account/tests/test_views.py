import pytest
from django.urls import reverse


@pytest.mark.django_db
def test_dashboard_view_is_reachable_without_an_active_savegame(logged_in_client):
    """
    Logging in leads straight here, so a user without a savegame sees this page first.
    """
    response = logged_in_client.get(reverse("account:dashboard-view"))

    assert response.status_code == 200
