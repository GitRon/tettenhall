import pytest
from django.test import RequestFactory
from django.urls import reverse

from apps.warband.navigation.context_processors import navigation


@pytest.mark.django_db
def test_navigation_offers_the_four_sections(logged_in_client, current_savegame):
    response = logged_in_client.get(reverse("warband:dashboard-view"))

    assert [section["key"] for section in response.context["nav_sections"]] == ["month", "warband", "town", "rivals"]


@pytest.mark.django_db
def test_navigation_marks_the_section_of_the_current_page(logged_in_client, current_savegame):
    response = logged_in_client.get(reverse("warband:town-upgrade-view"))

    assert response.context["current_nav_section"] == "town"


@pytest.mark.django_db
def test_navigation_offers_no_sections_without_a_savegame(logged_in_client):
    """
    There is no month to lay out yet, and the login page and the savegame list both carry their own
    way on.
    """
    response = logged_in_client.get(reverse("warband:dashboard-view"))

    assert response.context["nav_sections"] == []


@pytest.mark.django_db
def test_navigation_drops_the_faction_scoped_sections_without_a_player_faction(
    logged_in_client, savegame_without_player_faction
):
    """
    Two of the four entries are reversed with the player's own faction id, and a savegame can exist
    before its faction does - reversing either with an empty id raises, on every page.
    """
    response = logged_in_client.get(reverse("warband:dashboard-view"))

    assert [section["key"] for section in response.context["nav_sections"]] == ["month", "rivals"]


@pytest.mark.django_db
def test_navigation_offers_the_pages_of_the_current_section(logged_in_client, current_savegame):
    response = logged_in_client.get(reverse("warband:skirmish-list-view"))

    assert [page["label"] for page in response.context["nav_pages"]] == ["Rivals", "Skirmishes"]
    assert [page["is_current"] for page in response.context["nav_pages"]] == [False, True]


@pytest.mark.django_db
def test_navigation_offers_no_pages_for_a_section_that_is_one_page(logged_in_client, current_savegame):
    response = logged_in_client.get(reverse("warband:dashboard-view"))

    assert response.context["nav_pages"] == []


@pytest.mark.django_db
def test_navigation_marks_nothing_when_no_url_was_resolved(user, current_savegame):
    """
    A template rendered outside a request cycle has no resolver match to read a section off, and
    reversing the entries themselves still has to work.
    """
    request = RequestFactory().get("/")
    request.user = user

    result = navigation(request)

    assert result["current_nav_section"] is None
    assert result["nav_pages"] == []
