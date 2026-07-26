import pytest
from django.urls import reverse


@pytest.mark.django_db
def test_savegame_create_view_is_reachable_without_an_active_savegame(logged_in_client):
    """
    A user with no savegame has to be able to reach the page creating one. Since it renders the
    base template with its context processors, that page used to answer with a server error - which
    locked a fresh account out of the whole game.
    """
    response = logged_in_client.get(reverse("savegame:savegame-create-view"))

    assert response.status_code == 200


@pytest.mark.django_db
def test_savegame_list_view_is_reachable_without_an_active_savegame(logged_in_client):
    response = logged_in_client.get(reverse("savegame:savegame-list-view"))

    assert response.status_code == 200
