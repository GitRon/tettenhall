from html.parser import HTMLParser

import pytest
from django.urls import reverse

from apps.faction.tests.factories.faction import FactionFactory
from apps.finance.models.transaction import Transaction
from apps.item.tests.factories.item import ItemFactory
from apps.savegame.tests.factories.savegame import SavegameFactory
from apps.skirmish.models.warrior import Warrior
from apps.skirmish.tests.factories.warrior import WarriorFactory


def _swallowing_tags(*, html: str) -> list[str]:
    """
    Names of tags that ran into the next element because their own bracket was never closed.

    An unclosed opening tag makes the parser read everything up to the next ">" as its attributes,
    so the swallowed element shows up as an attribute whose name starts with "<".
    """
    offenders = []

    class _Parser(HTMLParser):
        def handle_starttag(self, tag: str, attrs: list) -> None:
            if any(name.startswith("<") for name, _ in attrs):
                offenders.append(tag)

    _Parser().feed(html)

    return offenders


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
def test_faction_detail_view_renders_well_formed_tags(logged_in_client, current_savegame):
    """
    The div wrapping the captured warrior list was missing its closing bracket. Django still renders
    the include - it works on template tags, not on HTML - so the damage only shows in the browser:
    the parser reads the whole nested element as attributes of the unclosed tag and the section
    disappears. Asserting on the parsed markup is what catches that.
    """
    faction = current_savegame.player_faction
    faction.leader = WarriorFactory(faction=faction)
    faction.save()

    response = logged_in_client.get(reverse("faction:faction-detail-view", kwargs={"pk": faction.id}))

    assert response.status_code == 200
    assert "Captured warriors" in response.content.decode()
    # An attribute name containing "<" means a tag swallowed the element following it
    assert _swallowing_tags(html=response.content.decode()) == []


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
