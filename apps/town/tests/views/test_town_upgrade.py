import pytest
from django.urls import reverse

from apps.faction.tests.factories.faction import FactionFactory
from apps.finance.models import Transaction
from apps.finance.tests.factories.transaction import TransactionFactory
from apps.savegame.tests.factories.savegame import SavegameFactory
from apps.town.models import Town


def _building(response, building_type: str) -> dict:
    """
    The entry the page renders for one building.
    """
    return next(
        building for building in response.context["building_list"] if building["building_type"] == building_type
    )


@pytest.mark.django_db
def test_town_upgrade_view_shows_the_town_of_the_player_faction(logged_in_client, current_savegame):
    response = logged_in_client.get(reverse("town:town-upgrade-view"))

    assert response.status_code == 200
    assert response.context["object"] == current_savegame.player_faction.town


@pytest.mark.django_db
def test_town_upgrade_view_offers_the_costs_of_the_next_level(logged_in_client, current_savegame):
    town = current_savegame.player_faction.town
    town.hall = Town.HallChoices.HALL_SMALL
    town.save()

    response = logged_in_client.get(reverse("town:town-upgrade-view"))

    assert response.status_code == 200
    # A Mead Hall is standing, so the Great Hall is what the page offers next
    assert _building(response, "hall")["costs"] == 2000


@pytest.mark.django_db
def test_town_upgrade_view_offers_every_building(logged_in_client, current_savegame):
    response = logged_in_client.get(reverse("town:town-upgrade-view"))

    assert [building["building_type"] for building in response.context["building_list"]] == [
        "hall",
        "weaponsmith",
        "marketplace",
        "sanctuary",
    ]


@pytest.mark.django_db
def test_town_upgrade_view_keeps_naming_a_price_at_the_maximum_level(logged_in_client, current_savegame):
    """
    The next level is capped at the top one, which would otherwise be looked up one above the
    largest variant.
    """
    town = current_savegame.player_faction.town
    town.hall = Town.HallChoices.HALL_LARGE
    town.save()

    response = logged_in_client.get(reverse("town:town-upgrade-view"))

    assert _building(response, "hall")["costs"] == 3000


@pytest.mark.django_db
def test_town_upgrade_view_does_not_show_a_town_of_another_savegame(logged_in_client, user):
    """
    get_object() used to resolve through super().get_queryset(), which skips the scoping and hands
    back the first town in the table - the oldest one, belonging to whoever created it.
    """
    # Created first, so an unscoped lookup picks this one
    FactionFactory()
    savegame = SavegameFactory(created_by=user)
    savegame.player_faction = FactionFactory(savegame=savegame)
    savegame.save()

    response = logged_in_client.get(reverse("town:town-upgrade-view"))

    assert response.status_code == 200
    assert response.context["object"] == savegame.player_faction.town


@pytest.mark.django_db
def test_town_upgrade_view_without_an_active_savegame(logged_in_client):
    """
    The town used to be dereferenced unguarded, so the page answered with a 500.
    """
    response = logged_in_client.get(reverse("town:town-upgrade-view"))

    assert response.status_code == 404


@pytest.mark.django_db
def test_upgrade_building_view_upgrades_the_building(logged_in_client, current_savegame):
    """
    Flow test: no mocking inside the chain, so this runs the real upgrade and asserts the end state.
    """
    town = current_savegame.player_faction.town
    town.last_constructed_building_at = 0
    town.save()
    TransactionFactory(faction=current_savegame.player_faction, amount=1000)

    response = logged_in_client.post(reverse("town:upgrade-building-view", kwargs={"building_type": "hall"}))

    assert response.status_code == 200
    town.refresh_from_db()
    assert town.hall == Town.HallChoices.HALL_SMALL


@pytest.mark.django_db
def test_upgrade_building_view_charges_the_building_costs(logged_in_client, current_savegame):
    town = current_savegame.player_faction.town
    town.last_constructed_building_at = 0
    town.save()
    TransactionFactory(faction=current_savegame.player_faction, amount=1000)

    logged_in_client.post(reverse("town:upgrade-building-view", kwargs={"building_type": "hall"}))

    assert Transaction.objects.current_balance(savegame_id=current_savegame.id) == 0


@pytest.mark.django_db
def test_upgrade_building_view_charges_the_costs_of_the_building_it_upgrades(logged_in_client, current_savegame):
    """
    Every building used to be priced through the hall, so the page advertised a weaponsmith at 0
    silver while the upgrade charged the hall's 1000.
    """
    town = current_savegame.player_faction.town
    town.weaponsmith = Town.WeaponsmithChoices.WEAPONSMITH_MEDIUM
    town.last_constructed_building_at = 0
    town.save()
    TransactionFactory(faction=current_savegame.player_faction, amount=3000)

    page = logged_in_client.get(reverse("town:town-upgrade-view"))
    logged_in_client.post(reverse("town:upgrade-building-view", kwargs={"building_type": "weaponsmith"}))

    # A Master Forge costs 3000, so the advertised price is what leaves the purse
    assert _building(page, "weaponsmith")["costs"] == 3000
    assert Transaction.objects.current_balance(savegame_id=current_savegame.id) == 0


@pytest.mark.django_db
def test_upgrade_building_view_upgrades_a_building_other_than_the_hall(logged_in_client, current_savegame):
    town = current_savegame.player_faction.town
    town.last_constructed_building_at = 0
    town.save()
    TransactionFactory(faction=current_savegame.player_faction, amount=1000)

    logged_in_client.post(reverse("town:upgrade-building-view", kwargs={"building_type": "sanctuary"}))

    town.refresh_from_db()
    assert town.sanctuary == Town.SanctuaryChoices.SANCTUARY_SMALL


@pytest.mark.django_db
def test_upgrade_building_view_at_the_maximum_level(logged_in_client, current_savegame):
    """
    The guard used to read "> 3", which the levels never reach, so the largest hall asked for a
    level above the last one and the lookup raised instead of answering with the warning.
    """
    town = current_savegame.player_faction.town
    town.hall = Town.HallChoices.HALL_LARGE
    town.last_constructed_building_at = 0
    town.save()

    response = logged_in_client.post(reverse("town:upgrade-building-view", kwargs={"building_type": "hall"}))

    assert response["HX-Redirect"] == reverse("town:town-upgrade-view")
    town.refresh_from_db()
    assert town.hall == Town.HallChoices.HALL_LARGE


@pytest.mark.django_db
def test_upgrade_building_view_without_enough_silver(logged_in_client, current_savegame):
    town = current_savegame.player_faction.town
    town.last_constructed_building_at = 0
    town.save()

    response = logged_in_client.post(reverse("town:upgrade-building-view", kwargs={"building_type": "hall"}))

    assert response.status_code == 200
    town.refresh_from_db()
    assert town.hall == Town.HallChoices.HALL_NONE


@pytest.mark.django_db
def test_upgrade_building_view_with_a_building_already_commissioned_this_month(logged_in_client, current_savegame):
    town = current_savegame.player_faction.town
    town.last_constructed_building_at = current_savegame.current_month
    town.save()
    TransactionFactory(faction=current_savegame.player_faction, amount=1000)

    response = logged_in_client.post(reverse("town:upgrade-building-view", kwargs={"building_type": "hall"}))

    assert response.status_code == 200
    town.refresh_from_db()
    assert town.hall == Town.HallChoices.HALL_NONE


@pytest.mark.django_db
def test_upgrade_building_view_with_an_unknown_building_type(logged_in_client, current_savegame):
    """
    The building type is a free string from the URL, so without the whitelist "faction_id" would be
    raised like a building level and hand the town to another faction.
    """
    response = logged_in_client.post(reverse("town:upgrade-building-view", kwargs={"building_type": "faction_id"}))

    assert response.status_code == 404
    assert current_savegame.player_faction.town.faction_id == current_savegame.player_faction_id


@pytest.mark.django_db
def test_upgrade_building_view_without_an_active_savegame(logged_in_client):
    response = logged_in_client.post(reverse("town:upgrade-building-view", kwargs={"building_type": "hall"}))

    assert response.status_code == 404


@pytest.mark.django_db
def test_upgrade_building_view_does_not_upgrade_a_town_of_another_savegame(logged_in_client, user):
    """
    Without the scoping the oldest town in the table is the one that gets built up - and paid for
    out of the current player's purse.
    """
    # Created first, so an unscoped lookup picks this one, and left ready to be built on so nothing
    # but the scoping stands between the request and it
    foreign_faction = FactionFactory(town__last_constructed_building_at=0)
    savegame = SavegameFactory(created_by=user)
    savegame.player_faction = FactionFactory(savegame=savegame)
    savegame.save()
    TransactionFactory(faction=savegame.player_faction, amount=1000)

    logged_in_client.post(reverse("town:upgrade-building-view", kwargs={"building_type": "hall"}))

    foreign_faction.town.refresh_from_db()
    assert foreign_faction.town.hall == Town.HallChoices.HALL_NONE
