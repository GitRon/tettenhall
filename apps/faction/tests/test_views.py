import pytest
from django.contrib.messages import get_messages
from django.urls import reverse

from apps.faction.models.faction import Faction
from apps.faction.tests.factories.faction import FactionFactory
from apps.finance.models.transaction import Transaction
from apps.item.tests.factories.item import ItemFactory
from apps.savegame.tests.factories.savegame import SavegameFactory
from apps.skirmish.models.skirmish import Skirmish
from apps.skirmish.models.warrior import Warrior
from apps.skirmish.tests.factories.skirmish import SkirmishFactory
from apps.skirmish.tests.factories.warrior import WarriorFactory


@pytest.fixture
def player_faction_ready_to_march(current_savegame) -> Faction:
    """
    The player's faction with a healthy, unbooked leader.

    Every attack needs one before anything about the target is looked at, so each case below would
    otherwise open with the same three lines and bury the rule it is actually about.
    """
    faction = current_savegame.player_faction
    faction.leader = WarriorFactory(faction=faction)
    faction.save()

    return faction


@pytest.mark.django_db
def test_faction_detail_view_shows_the_faction(logged_in_client, current_savegame):
    faction = current_savegame.player_faction
    # The template links to the leader unconditionally, so a faction without one cannot be rendered
    faction.leader = WarriorFactory(faction=faction)
    faction.save()

    response = logged_in_client.get(reverse("faction:faction-detail-view", kwargs={"pk": faction.id}))

    assert response.status_code == 200
    assert list(response.context["warrior_list"]) == [faction.leader]


@pytest.mark.django_db
def test_faction_detail_view_hides_factions_of_other_savegames(logged_in_client, current_savegame):
    other_savegame = SavegameFactory()
    foreign_faction = FactionFactory(savegame=other_savegame)

    response = logged_in_client.get(reverse("faction:faction-detail-view", kwargs={"pk": foreign_faction.id}))

    assert response.status_code == 404


@pytest.mark.django_db
def test_faction_detail_view_offers_an_attack_on_a_rival(
    logged_in_client, current_savegame, player_faction_ready_to_march
):
    rival_faction = FactionFactory(savegame=current_savegame)
    WarriorFactory(faction=rival_faction)

    response = logged_in_client.get(reverse("faction:faction-detail-view", kwargs={"pk": rival_faction.id}))

    assert response.status_code == 200
    assert response.context["can_be_attacked"] is True


@pytest.mark.django_db
def test_faction_detail_view_offers_no_attack_on_the_players_own_faction(
    logged_in_client, current_savegame, player_faction_ready_to_march
):
    response = logged_in_client.get(
        reverse("faction:faction-detail-view", kwargs={"pk": player_faction_ready_to_march.id})
    )

    assert response.status_code == 200
    assert response.context["can_be_attacked"] is False


@pytest.mark.django_db
def test_faction_detail_view_says_why_the_attack_is_gone(
    logged_in_client, current_savegame, player_faction_ready_to_march
):
    """
    The button simply vanishing teaches the player nothing, and "every warrior fights once a month"
    is the rule he is most likely to walk into without noticing.
    """
    rival_faction = FactionFactory(savegame=current_savegame)
    WarriorFactory(faction=rival_faction)
    skirmish = SkirmishFactory(
        player_faction=player_faction_ready_to_march,
        non_player_faction=rival_faction,
        victorious_faction=player_faction_ready_to_march,
        month=current_savegame.current_month,
    )
    skirmish.player_warriors.add(player_faction_ready_to_march.leader)

    response = logged_in_client.get(reverse("faction:faction-detail-view", kwargs={"pk": rival_faction.id}))

    assert response.context["can_be_attacked"] is False
    assert response.context["has_marched_this_month"] is True


@pytest.mark.django_db
def test_faction_detail_view_says_nothing_about_marching_on_the_players_own_faction(
    logged_in_client, current_savegame, player_faction_ready_to_march
):
    """
    You can never march on yourself, so "your warriors have already fought" is not the reason the
    button is missing - it was never on offer.
    """
    skirmish = SkirmishFactory(
        player_faction=player_faction_ready_to_march,
        non_player_faction=FactionFactory(savegame=current_savegame),
        victorious_faction=player_faction_ready_to_march,
        month=current_savegame.current_month,
    )
    skirmish.player_warriors.add(player_faction_ready_to_march.leader)

    response = logged_in_client.get(
        reverse("faction:faction-detail-view", kwargs={"pk": player_faction_ready_to_march.id})
    )

    assert response.context["can_be_attacked"] is False
    assert response.context["has_marched_this_month"] is False


@pytest.mark.django_db
def test_faction_detail_view_says_nothing_about_marching_on_a_defeated_faction(
    logged_in_client, current_savegame, player_faction_ready_to_march
):
    """
    Same again: a knocked-out faction is off the board whatever the player's war band is doing.
    """
    defeated_faction = FactionFactory(savegame=current_savegame, is_defeated=True)
    WarriorFactory(faction=defeated_faction)
    skirmish = SkirmishFactory(
        player_faction=player_faction_ready_to_march,
        non_player_faction=defeated_faction,
        victorious_faction=player_faction_ready_to_march,
        month=current_savegame.current_month,
    )
    skirmish.player_warriors.add(player_faction_ready_to_march.leader)

    response = logged_in_client.get(reverse("faction:faction-detail-view", kwargs={"pk": defeated_faction.id}))

    assert response.context["can_be_attacked"] is False
    assert response.context["has_marched_this_month"] is False


@pytest.mark.django_db
def test_faction_item_list_view_shows_the_faction(logged_in_client, current_savegame):
    response = logged_in_client.get(
        reverse("faction:faction-item-list-htmx", kwargs={"pk": current_savegame.player_faction.id})
    )

    assert response.status_code == 200
    assert response.context["object"] == current_savegame.player_faction


@pytest.mark.django_db
def test_faction_item_list_view_hides_factions_of_other_savegames(logged_in_client, current_savegame):
    other_savegame = SavegameFactory()
    foreign_faction = FactionFactory(savegame=other_savegame)

    response = logged_in_client.get(reverse("faction:faction-item-list-htmx", kwargs={"pk": foreign_faction.id}))

    assert response.status_code == 404


@pytest.mark.django_db
def test_faction_warrior_list_view_shows_the_living_warriors(logged_in_client, current_savegame):
    warrior = WarriorFactory(faction=current_savegame.player_faction)
    WarriorFactory(faction=current_savegame.player_faction, condition=Warrior.ConditionChoices.CONDITION_DEAD)

    response = logged_in_client.get(
        reverse("faction:faction-warrior-list-htmx", kwargs={"pk": current_savegame.player_faction.id})
    )

    assert response.status_code == 200
    assert list(response.context["warrior_list"]) == [warrior]


@pytest.mark.django_db
def test_faction_warrior_list_view_hides_factions_of_other_savegames(logged_in_client, current_savegame):
    other_savegame = SavegameFactory()
    foreign_faction = FactionFactory(savegame=other_savegame)

    response = logged_in_client.get(reverse("faction:faction-warrior-list-htmx", kwargs={"pk": foreign_faction.id}))

    assert response.status_code == 404


@pytest.mark.django_db
def test_faction_captured_warrior_list_view_shows_the_faction(logged_in_client, current_savegame):
    response = logged_in_client.get(
        reverse("faction:faction-captured-warrior-list-htmx", kwargs={"pk": current_savegame.player_faction.id})
    )

    assert response.status_code == 200
    assert response.context["object"] == current_savegame.player_faction


@pytest.mark.django_db
def test_faction_captured_warrior_list_view_hides_factions_of_other_savegames(logged_in_client, current_savegame):
    other_savegame = SavegameFactory()
    foreign_faction = FactionFactory(savegame=other_savegame)

    response = logged_in_client.get(
        reverse("faction:faction-captured-warrior-list-htmx", kwargs={"pk": foreign_faction.id})
    )

    assert response.status_code == 404


@pytest.mark.django_db
def test_draft_warrior_from_fyrd_view_drafts_a_warrior(logged_in_client, current_savegame, queuebie_registry):
    faction = current_savegame.player_faction
    faction.fyrd_reserve = 1
    faction.save()

    response = logged_in_client.post(reverse("faction:faction-draft-warrior-from-fyrd-view", kwargs={"pk": faction.id}))

    assert response.status_code == 200
    assert "HX-Trigger" in response.headers
    faction.refresh_from_db()
    assert faction.fyrd_reserve == 0
    assert Warrior.objects.filter(faction=faction).count() == 1
    assert Transaction.objects.filter(faction=faction).count() == 1


@pytest.mark.django_db
def test_draft_warrior_from_fyrd_view_hides_factions_of_other_savegames(
    logged_in_client, current_savegame, queuebie_registry
):
    other_savegame = SavegameFactory()
    foreign_faction = FactionFactory(savegame=other_savegame, fyrd_reserve=1)

    response = logged_in_client.post(
        reverse("faction:faction-draft-warrior-from-fyrd-view", kwargs={"pk": foreign_faction.id})
    )

    assert response.status_code == 404
    assert Warrior.objects.filter(faction=foreign_faction).exists() is False


@pytest.mark.django_db
def test_draft_warrior_from_fyrd_view_cannot_draft_into_a_rival_faction(
    logged_in_client, current_savegame, queuebie_registry
):
    """
    Drafting is a write on the faction from the URL, so the savegame is the wrong scope - it would
    draft into a rival and spend its fyrd reserve.
    """
    rival_faction = FactionFactory(savegame=current_savegame, fyrd_reserve=1)

    response = logged_in_client.post(
        reverse("faction:faction-draft-warrior-from-fyrd-view", kwargs={"pk": rival_faction.id})
    )

    assert response.status_code == 404
    rival_faction.refresh_from_db()
    assert rival_faction.fyrd_reserve == 1
    assert Warrior.objects.filter(faction=rival_faction).exists() is False


@pytest.mark.django_db
def test_draft_warrior_from_fyrd_view_without_a_player_faction(
    logged_in_client, savegame_without_player_faction, queuebie_registry
):
    """
    There is no own faction to draft into yet, so the scoping narrows to nothing.
    """
    faction = FactionFactory(savegame=savegame_without_player_faction, fyrd_reserve=1)

    response = logged_in_client.post(reverse("faction:faction-draft-warrior-from-fyrd-view", kwargs={"pk": faction.id}))

    assert response.status_code == 404
    assert Warrior.objects.filter(faction=faction).exists() is False


@pytest.mark.django_db
def test_faction_attack_view_shows_the_form(logged_in_client, current_savegame, player_faction_ready_to_march):
    rival_faction = FactionFactory(savegame=current_savegame)
    WarriorFactory(faction=rival_faction)

    response = logged_in_client.get(reverse("faction:faction-attack-view", kwargs={"pk": rival_faction.id}))

    assert response.status_code == 200
    assert response.context["object"] == rival_faction


@pytest.mark.django_db
def test_faction_attack_view_fights_the_rivals_own_war_band(
    logged_in_client, current_savegame, player_faction_ready_to_march, queuebie_registry
):
    """
    Flow test: no mocking inside the chain, so this runs the real queue and asserts the end state.
    The whole point of the story is on the second assertion - the defending side is the rival's own
    warriors, its leader among them, and not mercenaries invented for the fight.
    """
    follower = WarriorFactory(faction=player_faction_ready_to_march)
    rival_faction = FactionFactory(savegame=current_savegame)
    rival_leader = WarriorFactory(faction=rival_faction)
    rival_faction.leader = rival_leader
    rival_faction.save()

    response = logged_in_client.post(
        reverse("faction:faction-attack-view", kwargs={"pk": rival_faction.id}),
        data={"assigned_warriors": [follower.id]},
    )

    assert response.status_code == 302
    assert [str(message) for message in get_messages(response.wsgi_request)] == [
        f"Your war band marches on {rival_faction}."
    ]
    skirmish = Skirmish.objects.get(non_player_faction=rival_faction)
    assert list(skirmish.non_player_warriors.all()) == [rival_leader]
    assert list(skirmish.player_warriors.all()) == [player_faction_ready_to_march.leader, follower]
    assert skirmish.month == current_savegame.current_month


@pytest.mark.django_db
def test_faction_attack_view_hides_factions_of_other_savegames(
    logged_in_client, current_savegame, player_faction_ready_to_march
):
    other_savegame = SavegameFactory()
    foreign_faction = FactionFactory(savegame=other_savegame)
    WarriorFactory(faction=foreign_faction)

    response = logged_in_client.post(reverse("faction:faction-attack-view", kwargs={"pk": foreign_faction.id}), data={})

    assert response.status_code == 404
    assert Skirmish.objects.exists() is False


@pytest.mark.django_db
def test_faction_attack_view_cannot_attack_the_players_own_faction(
    logged_in_client, current_savegame, player_faction_ready_to_march
):
    """
    Scoping to the savegame still reaches the player's own faction, and marching on yourself would
    put the same warriors on both sides of the field.
    """
    response = logged_in_client.post(
        reverse("faction:faction-attack-view", kwargs={"pk": player_faction_ready_to_march.id}), data={}
    )

    assert response.status_code == 404
    assert Skirmish.objects.exists() is False


@pytest.mark.django_db
def test_faction_attack_view_cannot_attack_a_defeated_faction(
    logged_in_client, current_savegame, player_faction_ready_to_march
):
    """
    A knocked-out faction is off the board, so there is nothing left to march against.
    """
    defeated_faction = FactionFactory(savegame=current_savegame, is_defeated=True)
    WarriorFactory(faction=defeated_faction)

    response = logged_in_client.post(
        reverse("faction:faction-attack-view", kwargs={"pk": defeated_faction.id}), data={}
    )

    assert response.status_code == 404
    assert Skirmish.objects.exists() is False


@pytest.mark.django_db
def test_faction_attack_view_cannot_march_twice_in_a_month(
    logged_in_client, current_savegame, player_faction_ready_to_march
):
    """
    Every warrior fights once a month and the leader joins every attack, so one fight uses the month
    up - and it makes no difference that this is a rival nobody has touched yet.
    """
    already_fought = FactionFactory(savegame=current_savegame)
    fought_skirmish = SkirmishFactory(
        player_faction=player_faction_ready_to_march,
        non_player_faction=already_fought,
        victorious_faction=player_faction_ready_to_march,
        month=current_savegame.current_month,
    )
    fought_skirmish.player_warriors.add(player_faction_ready_to_march.leader)
    untouched_rival = FactionFactory(savegame=current_savegame)
    WarriorFactory(faction=untouched_rival)

    response = logged_in_client.post(reverse("faction:faction-attack-view", kwargs={"pk": untouched_rival.id}), data={})

    assert response.status_code == 404
    assert Skirmish.objects.count() == 1


@pytest.mark.django_db
def test_faction_attack_view_without_an_active_savegame(logged_in_client):
    """
    Answering 404 rather than a server error: with no savegame there is nothing to scope against.
    """
    faction = FactionFactory()

    response = logged_in_client.post(reverse("faction:faction-attack-view", kwargs={"pk": faction.pk}), data={})

    assert response.status_code == 404
    assert Skirmish.objects.exists() is False


@pytest.mark.django_db
def test_monthly_cost_overview_sums_up_the_salaries(logged_in_client, current_savegame):
    WarriorFactory(faction=current_savegame.player_faction, monthly_salary=30)
    WarriorFactory(faction=current_savegame.player_faction, monthly_salary=12)

    response = logged_in_client.get(
        reverse("faction:faction-monthly-costs-view", kwargs={"pk": current_savegame.player_faction.id})
    )

    assert response.status_code == 200
    assert response.context["monthly_salary_amount"] == 42


@pytest.mark.django_db
def test_monthly_cost_overview_hides_factions_of_other_savegames(logged_in_client, current_savegame):
    other_savegame = SavegameFactory()
    foreign_faction = FactionFactory(savegame=other_savegame)

    response = logged_in_client.get(reverse("faction:faction-monthly-costs-view", kwargs={"pk": foreign_faction.id}))

    assert response.status_code == 404


@pytest.mark.django_db
def test_town_square_view_shows_the_faction(logged_in_client, current_savegame):
    response = logged_in_client.get(
        reverse("faction:town-square-view", kwargs={"pk": current_savegame.player_faction.id})
    )

    assert response.status_code == 200
    assert response.context["object"] == current_savegame.player_faction


@pytest.mark.django_db
def test_town_square_view_hides_factions_of_other_savegames(logged_in_client, current_savegame):
    other_savegame = SavegameFactory()
    foreign_faction = FactionFactory(savegame=other_savegame)

    response = logged_in_client.get(reverse("faction:town-square-view", kwargs={"pk": foreign_faction.id}))

    assert response.status_code == 404


@pytest.mark.django_db
def test_faction_shop_item_list_view_shows_the_available_items(logged_in_client, current_savegame):
    shop_item = ItemFactory(savegame=current_savegame)
    current_savegame.player_faction.available_items.add(shop_item)

    response = logged_in_client.get(
        reverse("faction:shop-item-list-htmx", kwargs={"pk": current_savegame.player_faction.id})
    )

    assert response.status_code == 200
    assert list(response.context["item_list"]) == [shop_item]


@pytest.mark.django_db
def test_faction_shop_item_list_view_hides_factions_of_other_savegames(logged_in_client, current_savegame):
    other_savegame = SavegameFactory()
    foreign_faction = FactionFactory(savegame=other_savegame)

    response = logged_in_client.get(reverse("faction:shop-item-list-htmx", kwargs={"pk": foreign_faction.id}))

    assert response.status_code == 404


@pytest.mark.django_db
def test_town_square_view_without_an_active_savegame(logged_in_client):
    """
    Answering 404 rather than a server error: the mixin narrows to nothing when there is no savegame.
    """
    faction = FactionFactory()

    response = logged_in_client.get(reverse("faction:town-square-view", kwargs={"pk": faction.pk}))

    assert response.status_code == 404


@pytest.mark.django_db
def test_faction_detail_view_shows_a_faction_without_a_leader(logged_in_client, current_savegame):
    """
    Faction.leader is nullable, and reversing the warrior url with no id raises NoReverseMatch.
    """
    current_savegame.player_faction.leader = None
    current_savegame.player_faction.save()

    response = logged_in_client.get(
        reverse("faction:faction-detail-view", kwargs={"pk": current_savegame.player_faction.pk})
    )

    assert response.status_code == 200
