import pytest
from django.urls import reverse


@pytest.mark.django_db
def test_resource_bar_htmx_view_renders_the_counters(logged_in_client, current_savegame):
    response = logged_in_client.get(reverse("common:resource-bar-htmx"))

    assert response.status_code == 200
    assert response.context["current_savegame"] == current_savegame


@pytest.mark.django_db
def test_resource_bar_htmx_view_renders_without_a_player_faction(logged_in_client, savegame_without_player_faction):
    """
    A savegame exists before its faction does, and the bar's three counters all come from context
    processors that have to answer for that - so the fragment has to render rather than 500 the way
    every other authenticated page does.
    """
    response = logged_in_client.get(reverse("common:resource-bar-htmx"))

    assert response.status_code == 200
    assert response.context["current_balance"] == 0
