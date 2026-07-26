import pytest
from django.urls import reverse

from apps.faction.tests.factories.faction import FactionFactory
from apps.finance.models import Transaction
from apps.item.models.item_type import ItemType
from apps.item.tests.factories.item import ItemFactory
from apps.skirmish.tests.factories.warrior import WarriorFactory


@pytest.mark.django_db
def test_warrior_detail_view_shows_the_warrior(logged_in_client, current_savegame):
    warrior = WarriorFactory(faction=current_savegame.player_faction)

    response = logged_in_client.get(reverse("warrior:warrior-detail-view", kwargs={"pk": warrior.id}))

    assert response.status_code == 200
    assert response.context["warrior"] == warrior


@pytest.mark.django_db
def test_warrior_detail_view_hides_warriors_of_another_savegame(logged_in_client, current_savegame):
    foreign_warrior = WarriorFactory()

    response = logged_in_client.get(reverse("warrior:warrior-detail-view", kwargs={"pk": foreign_warrior.id}))

    assert response.status_code == 404


@pytest.mark.django_db
def test_warrior_weapon_update_view_renders_the_requested_field(logged_in_client, current_savegame):
    warrior = WarriorFactory(faction=current_savegame.player_faction)

    response = logged_in_client.get(
        reverse("warrior:warrior-partial-update-view", kwargs={"pk": warrior.id, "htmx_attribute": "weapon"})
    )

    assert response.status_code == 200
    assert response.context["attribute"] == "weapon"


@pytest.mark.django_db
def test_warrior_weapon_update_view_equips_the_chosen_weapon(logged_in_client, current_savegame):
    warrior = WarriorFactory(faction=current_savegame.player_faction)
    weapon = ItemFactory(
        type=ItemType.objects.get(name="Short sword"),
        owner=current_savegame.player_faction,
        savegame=current_savegame,
    )

    response = logged_in_client.post(
        reverse("warrior:warrior-partial-update-view", kwargs={"pk": warrior.id, "htmx_attribute": "weapon"}),
        data={"weapon": weapon.id},
    )

    assert response.status_code == 200
    warrior.refresh_from_db()
    assert warrior.weapon == weapon


@pytest.mark.django_db
def test_warrior_weapon_update_view_cannot_change_a_warrior_of_another_savegame(logged_in_client, current_savegame):
    foreign_warrior = WarriorFactory()
    weapon = ItemFactory(
        type=ItemType.objects.get(name="Short sword"),
        owner=foreign_warrior.faction,
        savegame=foreign_warrior.savegame,
    )

    response = logged_in_client.post(
        reverse("warrior:warrior-partial-update-view", kwargs={"pk": foreign_warrior.id, "htmx_attribute": "weapon"}),
        data={"weapon": weapon.id},
    )

    assert response.status_code == 404
    foreign_warrior.refresh_from_db()
    assert foreign_warrior.weapon is None


@pytest.mark.django_db
def test_warrior_recruit_captured_view_moves_the_captive_into_the_faction(logged_in_client, current_savegame):
    enemy_faction = FactionFactory(savegame=current_savegame)
    captive = WarriorFactory(faction=enemy_faction)
    current_savegame.player_faction.captured_warriors.add(captive)

    response = logged_in_client.post(
        reverse(
            "warrior:warrior-recruit-captured-view",
            kwargs={"pk": captive.id, "faction_id": current_savegame.player_faction.id},
        )
    )

    assert response.status_code == 200
    assert "HX-Trigger" in response.headers
    captive.refresh_from_db()
    assert captive.faction == current_savegame.player_faction
    assert list(current_savegame.player_faction.captured_warriors.all()) == []


@pytest.mark.django_db
def test_warrior_recruit_captured_view_cannot_recruit_a_captive_of_another_savegame(logged_in_client, current_savegame):
    foreign_warrior = WarriorFactory()

    response = logged_in_client.post(
        reverse(
            "warrior:warrior-recruit-captured-view",
            kwargs={"pk": foreign_warrior.id, "faction_id": current_savegame.player_faction.id},
        )
    )

    assert response.status_code == 404
    foreign_warrior.refresh_from_db()
    assert foreign_warrior.faction != current_savegame.player_faction


@pytest.mark.django_db
def test_warrior_enslave_captured_view_sells_the_captive(logged_in_client, current_savegame):
    enemy_faction = FactionFactory(savegame=current_savegame)
    captive = WarriorFactory(faction=enemy_faction, recruitment_price=100)
    current_savegame.player_faction.captured_warriors.add(captive)

    response = logged_in_client.post(
        reverse(
            "warrior:warrior-enslave-captured-view",
            kwargs={"pk": captive.id, "faction_id": current_savegame.player_faction.id},
        )
    )

    assert response.status_code == 200
    assert "HX-Trigger" in response.headers
    captive.refresh_from_db()
    assert captive.faction is None
    assert list(current_savegame.player_faction.captured_warriors.all()) == []
    assert Transaction.objects.get(faction=current_savegame.player_faction).amount == 50


@pytest.mark.django_db
def test_warrior_enslave_captured_view_cannot_enslave_a_captive_of_another_savegame(logged_in_client, current_savegame):
    foreign_warrior = WarriorFactory(recruitment_price=100)

    response = logged_in_client.post(
        reverse(
            "warrior:warrior-enslave-captured-view",
            kwargs={"pk": foreign_warrior.id, "faction_id": current_savegame.player_faction.id},
        )
    )

    assert response.status_code == 404
    foreign_warrior.refresh_from_db()
    assert foreign_warrior.faction is not None


@pytest.mark.django_db
def test_warrior_enslave_captured_view_cannot_enslave_a_warrior_who_is_not_a_captive(
    logged_in_client, current_savegame
):
    """
    remove_captive() is a silent no-op for a warrior that was never captured, so without this check
    a player could enslave his own warriors for silver.
    """
    own_warrior = WarriorFactory(faction=current_savegame.player_faction)

    response = logged_in_client.post(
        reverse(
            "warrior:warrior-enslave-captured-view",
            kwargs={"pk": own_warrior.id, "faction_id": current_savegame.player_faction.id},
        )
    )

    assert response.status_code == 404
    own_warrior.refresh_from_db()
    assert own_warrior.faction == current_savegame.player_faction


@pytest.mark.django_db
def test_warrior_recruit_captured_view_cannot_recruit_into_a_faction_of_another_savegame(
    logged_in_client, current_savegame
):
    """
    The faction id comes from the URL, so it has to be scoped as well - otherwise a captive could
    be handed to another player's faction.
    """
    foreign_faction = FactionFactory()
    captive = WarriorFactory(faction=current_savegame.player_faction)
    foreign_faction.captured_warriors.add(captive)

    response = logged_in_client.post(
        reverse(
            "warrior:warrior-recruit-captured-view",
            kwargs={"pk": captive.id, "faction_id": foreign_faction.id},
        )
    )

    assert response.status_code == 404
    captive.refresh_from_db()
    assert captive.faction == current_savegame.player_faction
