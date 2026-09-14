import pytest
from django.test import RequestFactory
from django.urls import resolve, reverse

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
def test_navigation_offers_no_pages_for_a_section_that_is_not_on_the_bar(user, savegame_without_player_faction):
    """
    Town is dropped without a player faction, so its page nav must not be offering Buildings under a
    section nothing names.

    Driven through the context processor rather than through a page, because there is no longer a
    town page that renders in this state - every one of them reads the faction off the savegame and
    answers 404 when there is none, and "404.html" does not extend "base.html". The guard is what
    stands between that and the day one of them does render.
    """
    request = RequestFactory().get("/town/shop")
    request.user = user
    request.resolver_match = resolve("/town/shop")

    result = navigation(request)

    assert result["current_nav_section"] == "town"
    assert result["nav_pages"] == []


@pytest.mark.django_db
def test_navigation_offers_the_five_pages_of_the_war_band(logged_in_client, current_savegame):
    """
    The landing page first, and the rest by how often a month makes the player open them.
    """
    response = logged_in_client.get(reverse("warband:warband-stores-view"))

    assert [page["label"] for page in response.context["nav_pages"]] == [
        "Warband",
        "Stores",
        "Fyrd",
        "Captives",
        "Progress",
    ]
    assert [page["is_current"] for page in response.context["nav_pages"]] == [False, True, False, False, False]


@pytest.mark.django_db
def test_navigation_offers_the_four_pages_of_the_town(logged_in_client, current_savegame):
    """
    The landing page first, then by how often a month makes the player open them - and Buildings last,
    because only one may be raised in a month.
    """
    response = logged_in_client.get(reverse("warband:town-board-view"))

    assert [page["label"] for page in response.context["nav_pages"]] == ["Shop", "Pub", "Board", "Buildings"]
    assert [page["is_current"] for page in response.context["nav_pages"]] == [False, False, True, False]


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
