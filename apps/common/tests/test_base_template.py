"""
Tests for the navbar in base.html, which every authenticated page extends.

A template error here is not confined to one view: it turns the whole site into a 500 for the
affected user, which is why the status code alone is worth asserting.
"""

import pytest
from django.urls import reverse


@pytest.mark.django_db
def test_dashboard_renders_without_a_player_faction(logged_in_client, savegame_without_player_faction):
    """
    The navbar reverses the faction and town-square urls from "current_savegame.player_faction_id".
    A savegame can exist before its faction does, and reversing either with an empty id raises
    NoReverseMatch - so every authenticated page answered 500.
    """
    response = logged_in_client.get(reverse("account:dashboard-view"))

    assert response.status_code == 200
