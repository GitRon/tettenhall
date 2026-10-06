from unittest import mock

import pytest
from django.contrib.messages import get_messages
from django.urls import reverse

from apps.common.tests.race import passes_first_time
from apps.warband.faction.models import Faction
from apps.warband.faction.tests.factories.faction import FactionFactory
from apps.warband.finance.models import Transaction
from apps.warband.finance.tests.factories.transaction import TransactionFactory
from apps.warband.month.models.player_month_log import PlayerMonthLog
from apps.warband.savegame.tests.factories.savegame import SavegameFactory
from apps.warband.skirmish.models.warrior import Warrior
from apps.warband.skirmish.tests.factories.warrior import WarriorFactory
from apps.warband.town.models import Town
from apps.warband.town.services.building_upgrade import UNAFFORDABLE_REFUSAL, get_building_upgrade_refusal
from apps.warband.town.services.feast import UNAFFORDABLE_FEAST_REFUSAL, get_feast_refusal
from apps.warband.town.services.geld import EMPTY_FYRD_REFUSAL, get_geld_refusal


def _building(response, building_type: str) -> dict:
    """
    The entry the page renders for one building.
    """
    return next(
        building for building in response.context["building_list"] if building["building_type"] == building_type
    )


@pytest.mark.django_db
def test_town_upgrade_view_shows_the_town_of_the_player_faction(logged_in_client, current_savegame):
    response = logged_in_client.get(reverse("warband:town-upgrade-view"))

    assert response.status_code == 200
    assert response.context["object"] == current_savegame.player_faction.town


@pytest.mark.django_db
def test_town_upgrade_view_offers_the_costs_of_the_next_level(logged_in_client, current_savegame):
    town = current_savegame.player_faction.town
    town.hall = Town.HallChoices.HALL_SMALL
    town.save()

    response = logged_in_client.get(reverse("warband:town-upgrade-view"))

    assert response.status_code == 200
    # A Mead Hall is standing, so the Great Hall is what the page offers next
    assert _building(response, "hall")["costs"] == 800


@pytest.mark.django_db
def test_town_upgrade_view_names_the_level_it_offers_next(logged_in_client, current_savegame):
    response = logged_in_client.get(reverse("warband:town-upgrade-view"))

    assert _building(response, "hall")["next_level_display"] == "Mead Hall"


@pytest.mark.django_db
def test_town_upgrade_view_puts_the_effects_of_both_levels_next_to_each_other(logged_in_client, current_savegame):
    """
    A price on its own says nothing about whether the building is worth it to the player now.
    """
    response = logged_in_client.get(reverse("warband:town-upgrade-view"))

    assert _building(response, "hall")["effect_list"] == [
        {"label": "Monthly income", "current": "50 silver", "next": "300 silver"},
        {"label": "Men needed for full income", "current": "0", "next": "1"},
        {"label": "Prisoners the cells hold", "current": "1", "next": "2"},
        {"label": "A feast mends a cut ceiling by", "current": "No feasts", "next": "10%"},
    ]


@pytest.mark.django_db
def test_town_upgrade_view_leaves_out_an_effect_the_next_level_does_not_move(logged_in_client, current_savegame):
    """
    The Mead Hall holds the single mercenary a hall-less town already holds, so a row for it would
    price a lever that is not moving. The two it does move stay.
    """
    response = logged_in_client.get(reverse("warband:town-upgrade-view"))

    assert [effect["label"] for effect in _building(response, "hall")["effect_list"]] == [
        "Monthly income",
        "Men needed for full income",
        "Prisoners the cells hold",
        "A feast mends a cut ceiling by",
    ]


@pytest.mark.django_db
def test_town_upgrade_view_keeps_every_effect_at_the_maximum_level(logged_in_client, current_savegame):
    """
    The top level is compared against itself, so every pair matches and filtering the matching ones
    would leave the one card whose effects are the whole point of it with nothing on it.
    """
    town = current_savegame.player_faction.town
    town.hall = Town.HallChoices.HALL_LARGE
    town.save()

    response = logged_in_client.get(reverse("warband:town-upgrade-view"))

    assert _building(response, "hall")["effect_list"] == [
        {"label": "Monthly income", "current": "750 silver", "next": "750 silver"},
        {"label": "Men needed for full income", "current": "3", "next": "3"},
        {"label": "Mercenaries in the pub", "current": "3", "next": "3"},
        {"label": "Prisoners the cells hold", "current": "4", "next": "4"},
        {"label": "A feast mends a cut ceiling by", "current": "30%", "next": "30%"},
        {"label": "Feast per man", "current": "15 silver", "next": "15 silver"},
    ]


@pytest.mark.django_db
def test_town_upgrade_view_with_enough_silver_for_the_next_level(logged_in_client, current_savegame):
    TransactionFactory(faction=current_savegame.player_faction, amount=600)

    response = logged_in_client.get(reverse("warband:town-upgrade-view"))

    assert _building(response, "hall")["can_afford"] is True


@pytest.mark.django_db
def test_town_upgrade_view_without_enough_silver_for_the_next_level(logged_in_client, current_savegame):
    """
    The page disables the button, so the price is answered before the click rather than by a warning
    notification that fades after a second.
    """
    TransactionFactory(faction=current_savegame.player_faction, amount=599)

    response = logged_in_client.get(reverse("warband:town-upgrade-view"))

    assert _building(response, "hall")["can_afford"] is False


@pytest.mark.django_db
def test_town_upgrade_view_names_the_month_before_the_price(logged_in_client, current_savegame):
    """
    The page asks the refusal the upgrade asks, in its order: a town that has built this month and
    cannot pay is told about the month, which is the one thing more silver would not change.
    """
    town = current_savegame.player_faction.town
    town.last_constructed_building_at = current_savegame.current_month
    town.save()

    response = logged_in_client.get(reverse("warband:town-upgrade-view"))

    assert (_building(response, "hall")["has_already_built"], _building(response, "hall")["can_afford"]) == (
        True,
        True,
    )


@pytest.mark.django_db
def test_town_upgrade_view_offers_every_building(logged_in_client, current_savegame):
    response = logged_in_client.get(reverse("warband:town-upgrade-view"))

    assert [building["building_type"] for building in response.context["building_list"]] == [
        "hall",
        "weaponsmith",
        "marketplace",
        "sanctuary",
        "fortification",
    ]


@pytest.mark.django_db
def test_town_upgrade_view_prices_the_first_wall(logged_in_client, current_savegame):
    response = logged_in_client.get(reverse("warband:town-upgrade-view"))

    fortification = _building(response, "fortification")
    assert (fortification["next_level_display"], fortification["costs"]) == ("Palisade", 500)


@pytest.mark.django_db
def test_town_upgrade_view_keeps_the_wall_strength_at_the_maximum_level(logged_in_client, current_savegame):
    town = current_savegame.player_faction.town
    town.fortification = Town.FortificationChoices.FORTIFICATION_LARGE
    town.save()

    response = logged_in_client.get(reverse("warband:town-upgrade-view"))

    assert _building(response, "fortification")["effect_list"] == [
        {"label": "Wall strength when marched on", "current": "50 points", "next": "50 points"},
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

    response = logged_in_client.get(reverse("warband:town-upgrade-view"))

    assert _building(response, "hall")["costs"] == 1600


@pytest.mark.django_db
def test_town_upgrade_view_does_not_show_a_town_of_another_savegame(logged_in_client, user):
    """
    get_object() has to resolve through the scoped queryset: super().get_queryset() skips the
    scoping and hands back the first town in the table - the oldest one, belonging to whoever
    created it.
    """
    # Created first, so an unscoped lookup picks this one
    FactionFactory()
    savegame = SavegameFactory(created_by=user)
    FactionFactory(savegame=savegame, is_player=True)

    response = logged_in_client.get(reverse("warband:town-upgrade-view"))

    assert response.status_code == 200
    assert response.context["object"] == savegame.player_faction.town


@pytest.mark.django_db
def test_town_upgrade_view_does_not_show_the_town_of_a_rival(logged_in_client, current_savegame):
    """
    A rival's town carries a non-zero sanctuary, so it is the one town in the savegame the URL could
    upgrade for free. The URL carries no id and PlayerTownMixin scopes to the player's faction, which
    is what keeps it out of reach.
    """
    rival = FactionFactory(savegame=current_savegame, town__sanctuary=Town.SanctuaryChoices.SANCTUARY_SMALL)

    response = logged_in_client.get(reverse("warband:town-upgrade-view"))

    assert response.context["object"] == current_savegame.player_faction.town
    assert response.context["object"] != rival.town


@pytest.mark.django_db
def test_town_upgrade_view_without_an_active_savegame(logged_in_client):
    """
    With no savegame there is no town to dereference, so the page answers 404 rather than a 500.
    """
    response = logged_in_client.get(reverse("warband:town-upgrade-view"))

    assert response.status_code == 404


@pytest.mark.django_db
def test_upgrade_building_view_upgrades_the_building(logged_in_client, current_savegame):
    """
    Flow test: no mocking inside the chain, so this runs the real upgrade and asserts the end state.
    """
    town = current_savegame.player_faction.town
    TransactionFactory(faction=current_savegame.player_faction, amount=900)

    response = logged_in_client.post(reverse("warband:upgrade-building-view", kwargs={"building_type": "hall"}))

    assert response.status_code == 200
    town.refresh_from_db()
    assert town.hall == Town.HallChoices.HALL_SMALL


@pytest.mark.django_db
def test_upgrade_building_view_charges_the_building_costs(logged_in_client, current_savegame):
    TransactionFactory(faction=current_savegame.player_faction, amount=600)

    logged_in_client.post(reverse("warband:upgrade-building-view", kwargs={"building_type": "hall"}))

    assert Transaction.objects.current_balance(faction_id=current_savegame.player_faction_id) == 0


@pytest.mark.django_db
def test_upgrade_building_view_charges_the_costs_of_the_building_it_upgrades(logged_in_client, current_savegame):
    """
    Each building is priced by its own level, not the hall's, so the price the page advertises is
    the one the upgrade charges.
    """
    town = current_savegame.player_faction.town
    town.weaponsmith = Town.WeaponsmithChoices.WEAPONSMITH_MEDIUM
    town.save()
    TransactionFactory(faction=current_savegame.player_faction, amount=1400)

    page = logged_in_client.get(reverse("warband:town-upgrade-view"))
    logged_in_client.post(reverse("warband:upgrade-building-view", kwargs={"building_type": "weaponsmith"}))

    # A Master Forge costs 1400, so the advertised price is what leaves the purse
    assert _building(page, "weaponsmith")["costs"] == 1400
    assert Transaction.objects.current_balance(faction_id=current_savegame.player_faction_id) == 0


@pytest.mark.django_db
def test_upgrade_building_view_upgrades_a_building_other_than_the_hall(logged_in_client, current_savegame):
    town = current_savegame.player_faction.town
    TransactionFactory(faction=current_savegame.player_faction, amount=900)

    logged_in_client.post(reverse("warband:upgrade-building-view", kwargs={"building_type": "sanctuary"}))

    town.refresh_from_db()
    assert town.sanctuary == Town.SanctuaryChoices.SANCTUARY_SMALL


@pytest.mark.django_db
def test_upgrade_building_view_raises_a_palisade(logged_in_client, current_savegame):
    town = current_savegame.player_faction.town
    TransactionFactory(faction=current_savegame.player_faction, amount=500)

    logged_in_client.post(reverse("warband:upgrade-building-view", kwargs={"building_type": "fortification"}))

    town.refresh_from_db()
    assert town.fortification == Town.FortificationChoices.FORTIFICATION_SMALL


@pytest.mark.django_db
def test_upgrade_building_view_at_the_maximum_level(logged_in_client, current_savegame):
    """
    The largest hall has no level above it, so the guard has to answer with the warning rather than
    ask the lookup for a level that does not exist, which raises.
    """
    town = current_savegame.player_faction.town
    town.hall = Town.HallChoices.HALL_LARGE
    town.save()

    response = logged_in_client.post(reverse("warband:upgrade-building-view", kwargs={"building_type": "hall"}))

    assert response["HX-Redirect"] == reverse("warband:town-upgrade-view")
    town.refresh_from_db()
    assert town.hall == Town.HallChoices.HALL_LARGE


@pytest.mark.django_db
def test_upgrade_building_view_without_enough_silver(logged_in_client, current_savegame):
    town = current_savegame.player_faction.town

    response = logged_in_client.post(reverse("warband:upgrade-building-view", kwargs={"building_type": "hall"}))

    assert response.status_code == 200
    town.refresh_from_db()
    assert town.hall == Town.HallChoices.HALL_NONE


@pytest.mark.django_db
def test_upgrade_building_view_with_a_building_already_commissioned_this_month(logged_in_client, current_savegame):
    town = current_savegame.player_faction.town
    town.last_constructed_building_at = current_savegame.current_month
    town.save()
    TransactionFactory(faction=current_savegame.player_faction, amount=900)

    response = logged_in_client.post(reverse("warband:upgrade-building-view", kwargs={"building_type": "hall"}))

    assert response.status_code == 200
    town.refresh_from_db()
    assert town.hall == Town.HallChoices.HALL_NONE


@pytest.mark.django_db
def test_upgrade_building_view_reports_the_month_before_the_missing_silver(logged_in_client, current_savegame):
    """
    Both guards apply to a player who has built this month and cannot pay either. Reporting the price
    sent them off to raise silver they cannot spend until the month is over.
    """
    town = current_savegame.player_faction.town
    town.last_constructed_building_at = current_savegame.current_month
    town.save()

    response = logged_in_client.post(reverse("warband:upgrade-building-view", kwargs={"building_type": "hall"}))

    assert [str(message) for message in get_messages(response.wsgi_request)] == [
        "You've already commissioned a building this month."
    ]


@pytest.mark.django_db
def test_upgrade_building_view_with_an_unknown_building_type(logged_in_client, current_savegame):
    """
    The building type is a free string from the URL, so without the whitelist "faction_id" would be
    raised like a building level and hand the town to another faction.
    """
    response = logged_in_client.post(reverse("warband:upgrade-building-view", kwargs={"building_type": "faction_id"}))

    assert response.status_code == 404
    assert current_savegame.player_faction.town.faction_id == current_savegame.player_faction_id


@pytest.mark.django_db
def test_upgrade_building_view_without_an_active_savegame(logged_in_client):
    response = logged_in_client.post(reverse("warband:upgrade-building-view", kwargs={"building_type": "hall"}))

    assert response.status_code == 404


@pytest.mark.django_db
def test_upgrade_building_view_does_not_upgrade_a_town_of_another_savegame(logged_in_client, user):
    """
    Without the scoping the oldest town in the table is the one that gets built up - and paid for
    out of the current player's purse.
    """
    # Created first, so an unscoped lookup picks this one up instead of the player's
    foreign_faction = FactionFactory()
    savegame = SavegameFactory(created_by=user)
    FactionFactory(savegame=savegame, is_player=True)
    TransactionFactory(faction=savegame.player_faction, amount=900)

    logged_in_client.post(reverse("warband:upgrade-building-view", kwargs={"building_type": "hall"}))

    # The player's own town is the one that moves - asserting only that the foreign town stands still
    # would also hold if the view had stopped upgrading anything at all
    savegame.player_faction.town.refresh_from_db()
    assert savegame.player_faction.town.hall == Town.HallChoices.HALL_SMALL
    foreign_faction.town.refresh_from_db()
    assert foreign_faction.town.hall == Town.HallChoices.HALL_NONE


def _feast_ready_town(current_savegame, *, silver: int = 900) -> Town:
    town = current_savegame.player_faction.town
    town.hall = Town.HallChoices.HALL_MEDIUM
    town.save()
    TransactionFactory(faction=current_savegame.player_faction, amount=silver)

    return town


@pytest.mark.django_db
def test_town_upgrade_view_prices_the_feast_for_the_war_band_as_it_stands(logged_in_client, current_savegame):
    _feast_ready_town(current_savegame)
    faction = current_savegame.player_faction
    WarriorFactory.create_batch(2, faction=faction, savegame=current_savegame, culture=faction.culture)
    head_count = faction.warriors.exclude_dead().count()

    response = logged_in_client.get(reverse("warband:town-upgrade-view"))

    assert response.context["feast"]["costs"] == head_count * 15


@pytest.mark.django_db
def test_throw_feast_view_mends_the_cut_charges_the_table_and_logs_it(logged_in_client, current_savegame):
    """
    Flow test through the whole chain: the month guard, the mending, the bill and the log line.
    """
    _feast_ready_town(current_savegame)
    faction = current_savegame.player_faction
    cut = WarriorFactory(
        faction=faction, savegame=current_savegame, culture=faction.culture, max_morale=10, peak_max_morale=20
    )
    head_count = faction.warriors.exclude_dead().count()

    response = logged_in_client.post(reverse("warband:throw-feast-view"))

    assert response.status_code == 200
    cut.refresh_from_db()
    assert (
        cut.max_morale,
        Transaction.objects.current_balance(faction_id=faction.id),
        PlayerMonthLog.objects.filter(faction=faction, kind=PlayerMonthLog.KindChoices.KIND_FEAST_THROWN).count(),
    ) == (12, 900 - head_count * 15, 1)


@pytest.mark.django_db
def test_throw_feast_view_neither_feeds_nor_charges_for_a_captive_or_the_dead(logged_in_client, current_savegame):
    _feast_ready_town(current_savegame)
    faction = current_savegame.player_faction
    head_count = faction.warriors.exclude_dead().count()
    captive = WarriorFactory(
        faction=None, savegame=current_savegame, culture=faction.culture, max_morale=10, peak_max_morale=20
    )
    faction.captured_warriors.add(captive)
    WarriorFactory(
        faction=faction,
        savegame=current_savegame,
        culture=faction.culture,
        condition=Warrior.ConditionChoices.CONDITION_DEAD,
    )

    logged_in_client.post(reverse("warband:throw-feast-view"))

    captive.refresh_from_db()
    assert (captive.max_morale, Transaction.objects.current_balance(faction_id=faction.id)) == (
        10,
        900 - head_count * 15,
    )


@pytest.mark.django_db
def test_throw_feast_view_feeds_and_charges_for_an_unpaid_man_without_lifting_him(logged_in_client, current_savegame):
    """
    He sits at the table, so he is on the bill - it is only the mending that passes him over.
    """
    _feast_ready_town(current_savegame)
    faction = current_savegame.player_faction
    head_count_without_him = faction.warriors.exclude_dead().count()
    unpaid = WarriorFactory(
        faction=faction,
        savegame=current_savegame,
        culture=faction.culture,
        max_morale=10,
        peak_max_morale=20,
        unpaid_months=1,
    )

    logged_in_client.post(reverse("warband:throw-feast-view"))

    unpaid.refresh_from_db()
    assert (unpaid.max_morale, Transaction.objects.current_balance(faction_id=faction.id)) == (
        10,
        900 - (head_count_without_him + 1) * 15,
    )


@pytest.mark.django_db
def test_throw_feast_view_refuses_a_town_without_a_hall(logged_in_client, current_savegame):
    """
    The button is disabled on the page, and a post that reaches the view anyway is refused there too.
    """
    TransactionFactory(faction=current_savegame.player_faction, amount=900)

    response = logged_in_client.post(reverse("warband:throw-feast-view"))

    assert [str(message) for message in get_messages(response.wsgi_request)] == [
        "There is no hall to feast in. Build one first."
    ]
    assert Transaction.objects.current_balance(faction_id=current_savegame.player_faction_id) == 900


@pytest.mark.django_db
def test_throw_feast_view_refuses_a_second_feast_in_the_same_month(logged_in_client, current_savegame):
    _feast_ready_town(current_savegame)
    logged_in_client.post(reverse("warband:throw-feast-view"))
    balance_after_the_first = Transaction.objects.current_balance(faction_id=current_savegame.player_faction_id)

    logged_in_client.post(reverse("warband:throw-feast-view"))

    assert Transaction.objects.current_balance(faction_id=current_savegame.player_faction_id) == (
        balance_after_the_first
    )


@pytest.mark.django_db
def test_upgrade_building_view_tells_the_loser_of_a_race_why_nothing_was_built(logged_in_client, current_savegame):
    """
    The request passed its check before another spend took the silver, so the handler turned it down.
    The line names the price rather than claiming a building - see "passes_first_time" for the staging.
    """
    with mock.patch(
        "apps.warband.town.views.town_upgrade.get_building_upgrade_refusal",
        side_effect=passes_first_time(get_building_upgrade_refusal),
    ):
        response = logged_in_client.post(reverse("warband:upgrade-building-view", kwargs={"building_type": "hall"}))

    assert [str(message) for message in get_messages(response.wsgi_request)] == [UNAFFORDABLE_REFUSAL]
    town = Town.objects.get(faction=current_savegame.player_faction)
    assert town.hall == Town.HallChoices.HALL_NONE


@pytest.mark.django_db
def test_throw_feast_view_tells_the_loser_of_a_race_why_nobody_ate(logged_in_client, current_savegame):
    """
    The request passed its check before another spend took the silver, so the handler turned it down.
    """
    town = current_savegame.player_faction.town
    town.hall = Town.HallChoices.HALL_SMALL
    town.save()
    WarriorFactory(faction=current_savegame.player_faction)

    with mock.patch(
        "apps.warband.town.views.town_upgrade.get_feast_refusal",
        side_effect=passes_first_time(get_feast_refusal),
    ):
        response = logged_in_client.post(reverse("warband:throw-feast-view"))

    assert [str(message) for message in get_messages(response.wsgi_request)] == [UNAFFORDABLE_FEAST_REFUSAL]
    town.refresh_from_db()
    assert town.last_feast_at == 0


def _with_fyrd(current_savegame, *, fyrd_reserve: int) -> Faction:
    faction = current_savegame.player_faction
    faction.fyrd_reserve = fyrd_reserve
    faction.save()

    return faction


@pytest.mark.django_db
def test_town_upgrade_view_offers_a_geld_while_there_is_a_name_on_the_roll(logged_in_client, current_savegame):
    _with_fyrd(current_savegame, fyrd_reserve=2)

    response = logged_in_client.get(reverse("warband:town-upgrade-view"))

    assert response.context["geld"] == {
        "silver": 80,
        "fyrd_names": 1,
        "fyrd_reserve": 2,
        "has_gelded": False,
        "can_geld": True,
    }


@pytest.mark.django_db
def test_town_upgrade_view_says_the_geld_was_already_called(logged_in_client, current_savegame):
    faction = _with_fyrd(current_savegame, fyrd_reserve=2)
    faction.town.last_geld_at = current_savegame.current_month
    faction.town.save()

    response = logged_in_client.get(reverse("warband:town-upgrade-view"))

    assert (response.context["geld"]["has_gelded"], response.context["geld"]["can_geld"]) == (True, False)


@pytest.mark.django_db
def test_call_geld_view_pays_the_silver_strikes_the_name_and_logs_it(logged_in_client, current_savegame):
    """
    Flow test through the whole chain: the month guard, the ledger, the roll and the log line.
    """
    faction = _with_fyrd(current_savegame, fyrd_reserve=2)
    balance_before = Transaction.objects.current_balance(faction_id=faction.id)

    response = logged_in_client.post(reverse("warband:call-geld-view"))

    assert response.status_code == 200
    faction.refresh_from_db()
    faction.town.refresh_from_db()
    assert (
        Transaction.objects.current_balance(faction_id=faction.id) - balance_before,
        faction.fyrd_reserve,
        faction.town.last_geld_at,
        PlayerMonthLog.objects.filter(faction=faction, kind=PlayerMonthLog.KindChoices.KIND_GELD_CALLED).count(),
    ) == (80, 1, current_savegame.current_month, 1)


@pytest.mark.django_db
def test_call_geld_view_refuses_a_second_geld_in_the_same_month(logged_in_client, current_savegame):
    faction = _with_fyrd(current_savegame, fyrd_reserve=2)
    logged_in_client.post(reverse("warband:call-geld-view"))
    balance_after_the_first = Transaction.objects.current_balance(faction_id=faction.id)

    logged_in_client.post(reverse("warband:call-geld-view"))

    faction.refresh_from_db()
    assert (Transaction.objects.current_balance(faction_id=faction.id), faction.fyrd_reserve) == (
        balance_after_the_first,
        1,
    )


@pytest.mark.django_db
def test_call_geld_view_refuses_with_nobody_on_the_roll(logged_in_client, current_savegame):
    """
    The button is disabled on the page, and a post that reaches the view anyway is refused there too.
    """
    _with_fyrd(current_savegame, fyrd_reserve=0)

    response = logged_in_client.post(reverse("warband:call-geld-view"))

    assert [str(message) for message in get_messages(response.wsgi_request)] == [EMPTY_FYRD_REFUSAL]


@pytest.mark.django_db
def test_call_geld_view_tells_the_loser_of_a_race_why_the_village_paid_nothing(logged_in_client, current_savegame):
    """
    The request passed its check before a draft took the last name, so the handler turned it down.
    """
    faction = _with_fyrd(current_savegame, fyrd_reserve=0)

    with mock.patch(
        "apps.warband.town.views.town_upgrade.get_geld_refusal",
        side_effect=passes_first_time(get_geld_refusal),
    ):
        response = logged_in_client.post(reverse("warband:call-geld-view"))

    assert [str(message) for message in get_messages(response.wsgi_request)] == [EMPTY_FYRD_REFUSAL]
    faction.town.refresh_from_db()
    assert faction.town.last_geld_at == 0
