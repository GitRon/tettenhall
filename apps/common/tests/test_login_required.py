import pytest
from django.urls import reverse


@pytest.mark.django_db
def test_anonymous_request_is_redirected_to_the_login_view(client):
    """
    Every view sits behind LoginRequiredMiddleware. Asserting that project-wide once is enough -
    per-view tests would only re-test framework behaviour.
    """
    response = client.get(reverse("savegame:savegame-list-view"))

    assert response.status_code == 302
    assert reverse("account:login-view") in response.url
