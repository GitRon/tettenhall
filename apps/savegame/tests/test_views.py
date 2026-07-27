from unittest import mock

import pytest
from django.urls import reverse

from apps.account.tests.factories.user import UserFactory
from apps.faction.models import Culture, Faction
from apps.savegame.models.savegame import Savegame
from apps.savegame.tests.factories.savegame import SavegameFactory


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
def test_savegame_create_view_bootstraps_a_whole_game(logged_in_client, user):
    """
    Flow test: creating a savegame kicks off the longest chain in the project, from the savegame
    itself down to the leader, shop items and quests of every faction in it. No mocking inside the
    chain, only the randomness at its edges, so the counts below are deterministic.
    """
    culture = Culture.objects.first()

    with (
        # Draws the number of rival factions and the fyrd reserve of every faction
        mock.patch("apps.faction.handlers.commands.faction.random.randint", return_value=3),
        # Draws the number of shop items, pub mercenaries and bulletin board quests per faction
        mock.patch("apps.faction.handlers.commands.faction.random.randrange", return_value=2),
    ):
        response = logged_in_client.post(
            reverse("savegame:savegame-create-view"),
            data={"town_name": "Winchester", "faction_name": "Wessex", "faction_culture": culture.id},
        )

    assert response.status_code == 302
    savegame = Savegame.objects.get(created_by=user)
    assert savegame.is_active is True
    assert savegame.player_faction.name == "Wessex"
    assert savegame.player_faction.town_name == "Winchester"
    assert savegame.player_faction.culture == culture
    # The player faction plus the three drawn rivals
    assert Faction.objects.filter(savegame=savegame).count() == 4
    assert savegame.player_faction.leader is not None
    assert savegame.player_faction.available_items.count() == 2
    assert savegame.player_faction.available_quests.count() == 2


@pytest.mark.django_db
def test_savegame_list_view_is_reachable_without_an_active_savegame(logged_in_client):
    response = logged_in_client.get(reverse("savegame:savegame-list-view"))

    assert response.status_code == 200


@pytest.mark.django_db
def test_savegame_list_view_lists_the_savegames_of_the_user(logged_in_client, current_savegame):
    response = logged_in_client.get(reverse("savegame:savegame-list-view"))

    assert response.status_code == 200
    assert list(response.context["savegame_list"]) == [current_savegame]


@pytest.mark.django_db
def test_savegame_list_view_hides_savegames_of_another_user(logged_in_client, current_savegame):
    """
    This view scopes by user instead of by savegame - picking a savegame is what it is for.
    """
    SavegameFactory(created_by=UserFactory())

    response = logged_in_client.get(reverse("savegame:savegame-list-view"))

    assert response.status_code == 200
    assert list(response.context["savegame_list"]) == [current_savegame]


@pytest.mark.django_db
def test_savegame_load_view_activates_the_savegame(logged_in_client, user, current_savegame):
    savegame_to_load = SavegameFactory(created_by=user, is_active=False)

    response = logged_in_client.post(reverse("savegame:savegame-load-view", kwargs={"pk": savegame_to_load.pk}))

    assert response.status_code == 200
    assert response["HX-Redirect"] == reverse("account:dashboard-view")
    savegame_to_load.refresh_from_db()
    assert savegame_to_load.is_active is True
    current_savegame.refresh_from_db()
    assert current_savegame.is_active is False


@pytest.mark.django_db
def test_savegame_load_view_cannot_load_a_savegame_of_another_user(logged_in_client):
    """
    Without the scoping by user the id from the URL would be enough to load a foreign savegame.
    """
    savegame_of_other_user = SavegameFactory(created_by=UserFactory(), is_active=False)

    response = logged_in_client.post(reverse("savegame:savegame-load-view", kwargs={"pk": savegame_of_other_user.pk}))

    assert response.status_code == 404
    savegame_of_other_user.refresh_from_db()
    assert savegame_of_other_user.is_active is False
