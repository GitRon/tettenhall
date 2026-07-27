"""
Tests for the navbar in base.html, which every authenticated page extends.

A template error here is not confined to one view: it turns the whole site into a 500 for the
affected user.
"""

import pytest
from django.urls import reverse


@pytest.mark.django_db
def test_navbar_links_to_the_player_faction(logged_in_client, current_savegame):
    response = logged_in_client.get(reverse("account:dashboard-view"))

    assert response.status_code == 200
    content = response.content.decode()
    assert reverse("faction:faction-detail-view", args=(current_savegame.player_faction_id,)) in content
    assert reverse("faction:town-square-view", args=(current_savegame.player_faction_id,)) in content


@pytest.mark.django_db
def test_navbar_omits_the_faction_links_without_a_player_faction(logged_in_client, savegame_without_player_faction):
    """
    A savegame can exist before its faction does, and reversing either url with an empty id raises
    NoReverseMatch - so every authenticated page answered 500.
    """
    response = logged_in_client.get(reverse("account:dashboard-view"))

    assert response.status_code == 200
    assert savegame_without_player_faction.player_faction_id is None
    assert "town-square" not in response.content.decode()
