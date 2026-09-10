import pytest
from django.urls import reverse

from apps.warband.faction.tests.factories.faction import FactionFactory
from apps.warband.finance.models import Transaction
from apps.warband.finance.tests.factories.transaction import TransactionFactory
from apps.warband.item.models.item_type import ItemType
from apps.warband.item.tests.factories.item import ItemFactory
from apps.warband.skirmish.models.warrior import Warrior
from apps.warband.skirmish.tests.factories.warrior import WarriorFactory


@pytest.mark.django_db
def test_warrior_detail_view_shows_the_warrior(logged_in_client, current_savegame):
    warrior = WarriorFactory(faction=current_savegame.player_faction)

    response = logged_in_client.get(reverse("warband:warrior-detail-view", kwargs={"pk": warrior.id}))

    assert response.status_code == 200
    assert response.context["warrior"] == warrior


@pytest.mark.django_db
def test_warrior_detail_view_hides_warriors_of_another_savegame(logged_in_client, current_savegame):
    foreign_warrior = WarriorFactory()

    response = logged_in_client.get(reverse("warband:warrior-detail-view", kwargs={"pk": foreign_warrior.id}))

    assert response.status_code == 404


@pytest.mark.django_db
def test_warrior_weapon_update_view_renders_the_requested_field(logged_in_client, current_savegame):
    warrior = WarriorFactory(faction=current_savegame.player_faction)

    response = logged_in_client.get(
        reverse("warband:warrior-partial-update-view", kwargs={"pk": warrior.id, "htmx_attribute": "weapon"})
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
        reverse("warband:warrior-partial-update-view", kwargs={"pk": warrior.id, "htmx_attribute": "weapon"}),
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
        reverse("warband:warrior-partial-update-view", kwargs={"pk": foreign_warrior.id, "htmx_attribute": "weapon"}),
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
            "warband:warrior-recruit-captured-view",
            kwargs={"pk": captive.id, "faction_id": current_savegame.player_faction.id},
        )
    )

    assert response.status_code == 200
    assert "HX-Trigger" in response.headers
    captive.refresh_from_db()
    assert captive.faction == current_savegame.player_faction
    assert list(current_savegame.player_faction.captured_warriors.all()) == []


@pytest.mark.django_db
def test_warrior_recruit_captured_view_marches_a_drained_captive_out_with_his_nerve_back(
    logged_in_client, current_savegame
):
    """
    The whole chain, because the morale half of it only fires for a captive the fight emptied, and
    the log entry it raises runs behind the database blocker - which a direct handler call lifts.
    """
    enemy_faction = FactionFactory(savegame=current_savegame)
    captive = WarriorFactory(faction=enemy_faction, current_morale=0, max_morale=20)
    current_savegame.player_faction.captured_warriors.add(captive)

    response = logged_in_client.post(
        reverse(
            "warband:warrior-recruit-captured-view",
            kwargs={"pk": captive.id, "faction_id": current_savegame.player_faction.id},
        )
    )

    assert response.status_code == 200
    captive.refresh_from_db()
    assert captive.current_morale == 15


@pytest.mark.django_db
def test_warrior_recruit_captured_view_cannot_recruit_a_captive_of_another_savegame(logged_in_client, current_savegame):
    foreign_warrior = WarriorFactory()

    response = logged_in_client.post(
        reverse(
            "warband:warrior-recruit-captured-view",
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
            "warband:warrior-enslave-captured-view",
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
            "warband:warrior-enslave-captured-view",
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
            "warband:warrior-enslave-captured-view",
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
            "warband:warrior-recruit-captured-view",
            kwargs={"pk": captive.id, "faction_id": foreign_faction.id},
        )
    )

    assert response.status_code == 404
    captive.refresh_from_db()
    assert captive.faction == current_savegame.player_faction


@pytest.mark.django_db
def test_warrior_recruit_captured_view_cannot_recruit_into_a_rival_faction(logged_in_client, current_savegame):
    """
    Being in the player's savegame is not enough: a rival is a faction of it, and recruiting his
    captive staffed the rival's own war band for free, on the player's click.
    """
    rival_faction = FactionFactory(savegame=current_savegame)
    third_party = FactionFactory(savegame=current_savegame)
    captive = WarriorFactory(faction=third_party, savegame=current_savegame)
    rival_faction.captured_warriors.add(captive)

    response = logged_in_client.post(
        reverse(
            "warband:warrior-recruit-captured-view",
            kwargs={"pk": captive.id, "faction_id": rival_faction.id},
        )
    )

    assert response.status_code == 404
    assert list(rival_faction.captured_warriors.all()) == [captive]


@pytest.mark.django_db
def test_warrior_enslave_captured_view_cannot_enslave_a_rivals_captive(logged_in_client, current_savegame):
    """
    The transaction is written for the faction holding the prisoner, so this used to pay a rival for
    selling his own captive.
    """
    rival_faction = FactionFactory(savegame=current_savegame)
    third_party = FactionFactory(savegame=current_savegame)
    captive = WarriorFactory(faction=third_party, savegame=current_savegame, recruitment_price=200)
    rival_faction.captured_warriors.add(captive)

    response = logged_in_client.post(
        reverse(
            "warband:warrior-enslave-captured-view",
            kwargs={"pk": captive.id, "faction_id": rival_faction.id},
        )
    )

    assert response.status_code == 404
    assert Transaction.objects.current_balance(faction_id=rival_faction.id) == 0


@pytest.mark.django_db
def test_warrior_recruit_captured_view_without_a_player_faction(logged_in_client, savegame_without_player_faction):
    """
    Nothing is the player's yet, so there is no faction he may act for.
    """
    faction = FactionFactory(savegame=savegame_without_player_faction)
    captive = WarriorFactory(faction=faction, savegame=savegame_without_player_faction)
    faction.captured_warriors.add(captive)

    response = logged_in_client.post(
        reverse("warband:warrior-recruit-captured-view", kwargs={"pk": captive.id, "faction_id": faction.id})
    )

    assert response.status_code == 404
    assert list(faction.captured_warriors.all()) == [captive]


@pytest.mark.django_db
def test_warrior_weapon_update_view_cannot_rearm_a_rival_warrior(logged_in_client, current_savegame):
    """
    Changing what a warrior carries is a write, and a rival's men are in the player's savegame - so
    the URL was all it took to re-arm them.
    """
    rival_faction = FactionFactory(savegame=current_savegame)
    rival_warrior = WarriorFactory(faction=rival_faction, savegame=current_savegame, weapon=None)
    weapon = ItemFactory(savegame=current_savegame, owner=rival_faction)

    response = logged_in_client.post(
        reverse(
            "warband:warrior-partial-update-view",
            kwargs={"pk": rival_warrior.id, "htmx_attribute": "weapon"},
        ),
        data={"weapon": weapon.id},
    )

    assert response.status_code == 404
    rival_warrior.refresh_from_db()
    assert rival_warrior.weapon is None


@pytest.mark.django_db
def test_warrior_detail_view_shows_the_gear_of_the_players_own_warrior(logged_in_client, current_savegame):
    warrior = WarriorFactory(faction=current_savegame.player_faction)

    response = logged_in_client.get(reverse("warband:warrior-detail-view", kwargs={"pk": warrior.id}))

    assert response.status_code == 200
    assert response.context["can_see_gear"] is True


@pytest.mark.django_db
def test_warrior_detail_view_shows_the_gear_of_a_captive_the_player_holds(logged_in_client, current_savegame):
    """
    A prisoner carries no faction at all, so asking whether he is "in the player's faction" would
    withhold the gear of a man the player is holding and about to recruit or sell.
    """
    captive = WarriorFactory(faction=None, savegame=current_savegame, culture=current_savegame.player_faction.culture)
    current_savegame.player_faction.captured_warriors.add(captive)

    response = logged_in_client.get(reverse("warband:warrior-detail-view", kwargs={"pk": captive.id}))

    assert response.status_code == 200
    assert response.context["can_see_gear"] is True


@pytest.mark.django_db
def test_warrior_detail_view_shows_the_gear_of_a_mercenary_in_the_players_pub(logged_in_client, current_savegame):
    """
    The pub card already names the weapon it is charging for, so hiding it one click later would
    contradict the screen the player just came from.
    """
    mercenary = WarriorFactory(faction=None, savegame=current_savegame, culture=current_savegame.player_faction.culture)
    current_savegame.player_faction.available_mercenaries.add(mercenary)

    response = logged_in_client.get(reverse("warband:warrior-detail-view", kwargs={"pk": mercenary.id}))

    assert response.status_code == 200
    assert response.context["can_see_gear"] is True


@pytest.mark.django_db
def test_warrior_detail_view_hides_the_gear_of_a_captive_a_rival_holds(logged_in_client, current_savegame):
    """
    A rival's prisoner is faction-less too, so "no faction" cannot be the test either.
    """
    rival_faction = FactionFactory(savegame=current_savegame)
    captive = WarriorFactory(faction=None, savegame=current_savegame, culture=rival_faction.culture)
    rival_faction.captured_warriors.add(captive)

    response = logged_in_client.get(reverse("warband:warrior-detail-view", kwargs={"pk": captive.id}))

    assert response.status_code == 200
    assert response.context["can_see_gear"] is False


@pytest.mark.django_db
def test_warrior_detail_view_offers_the_gear_edit_for_the_players_own_warrior(logged_in_client, current_savegame):
    warrior = WarriorFactory(faction=current_savegame.player_faction)

    response = logged_in_client.get(reverse("warband:warrior-detail-view", kwargs={"pk": warrior.id}))

    assert response.status_code == 200
    assert response.context["can_edit_gear"] is True


@pytest.mark.django_db
def test_warrior_detail_view_does_not_offer_the_gear_edit_for_a_captive(logged_in_client, current_savegame):
    """
    His gear is readable and his loadout is not the player's to change: the update view resolves the
    player's own faction only, so an edit control here could answer nothing but 404.
    """
    captive = WarriorFactory(faction=None, savegame=current_savegame, culture=current_savegame.player_faction.culture)
    current_savegame.player_faction.captured_warriors.add(captive)

    response = logged_in_client.get(reverse("warband:warrior-detail-view", kwargs={"pk": captive.id}))

    assert response.status_code == 200
    assert response.context["can_see_gear"] is True
    assert response.context["can_edit_gear"] is False


@pytest.mark.django_db
def test_warrior_weapon_update_view_refuses_a_captive(logged_in_client, current_savegame):
    """
    The other half of the same rule, asked of the view rather than the page.
    """
    captive = WarriorFactory(faction=None, savegame=current_savegame, culture=current_savegame.player_faction.culture)
    current_savegame.player_faction.captured_warriors.add(captive)

    response = logged_in_client.get(
        reverse(
            "warband:warrior-partial-update-view",
            kwargs={"pk": captive.id, "htmx_attribute": "weapon"},
        )
    )

    assert response.status_code == 404


@pytest.mark.django_db
def test_warrior_detail_view_hides_the_gear_of_a_rival_warrior(logged_in_client, current_savegame):
    """
    This page is where a rival card's "Detail" link leads, so withholding gear on the card alone
    would only have cost the player a click.
    """
    rival_faction = FactionFactory(savegame=current_savegame)
    rival_warrior = WarriorFactory(faction=rival_faction, savegame=current_savegame)

    response = logged_in_client.get(reverse("warband:warrior-detail-view", kwargs={"pk": rival_warrior.id}))

    assert response.status_code == 200
    assert response.context["can_see_gear"] is False


@pytest.mark.django_db
def test_warrior_detail_view_shows_the_health_of_the_players_own_warrior(logged_in_client, current_savegame):
    """
    Health and morale are the two the rivals list calls knowledge not earned without scouting, so
    the page gates them on the same predicate the roster card does - and no more than the card
    does, or "Detail" would go back to showing less than the tile that links to it.
    """
    warrior = WarriorFactory(faction=current_savegame.player_faction)

    response = logged_in_client.get(reverse("warband:warrior-detail-view", kwargs={"pk": warrior.id}))

    assert response.status_code == 200
    assert response.context["is_player_faction"] is True


@pytest.mark.django_db
def test_warrior_detail_view_hides_the_health_of_a_captive(logged_in_client, current_savegame):
    """
    A prisoner's gear is readable and his health is not: he carries no faction, so the gear gate
    lets him through on the strength of who holds him and this one does not.
    """
    captive = WarriorFactory(faction=None, savegame=current_savegame, culture=current_savegame.player_faction.culture)
    current_savegame.player_faction.captured_warriors.add(captive)

    response = logged_in_client.get(reverse("warband:warrior-detail-view", kwargs={"pk": captive.id}))

    assert response.status_code == 200
    assert response.context["is_player_faction"] is False


@pytest.mark.django_db
def test_warrior_detail_view_says_how_long_the_player_has_left_him_unpaid(logged_in_client, current_savegame):
    warrior = WarriorFactory(faction=current_savegame.player_faction, unpaid_months=2)

    response = logged_in_client.get(reverse("warband:warrior-detail-view", kwargs={"pk": warrior.id}))

    assert response.status_code == 200
    assert response.context["unpaid_wages_note"] == "2 of 3 unpaid months"


@pytest.mark.django_db
def test_warrior_detail_view_says_nothing_about_a_rivals_wage_troubles(logged_in_client, current_savegame):
    """
    A rival's payroll is #90's question. The card withholds it, and this page is where the card's
    "Detail" link leads.
    """
    rival_faction = FactionFactory(savegame=current_savegame)
    rival_warrior = WarriorFactory(faction=rival_faction, savegame=current_savegame, unpaid_months=2)

    response = logged_in_client.get(reverse("warband:warrior-detail-view", kwargs={"pk": rival_warrior.id}))

    assert response.status_code == 200
    assert response.context["unpaid_wages_note"] is None


@pytest.mark.django_db
def test_warrior_weapon_update_view_rejects_an_unknown_attribute(logged_in_client, current_savegame):
    """
    The attribute is a free URL segment, so a hand-typed one used to reach a RuntimeError in the
    form and answer 500 where 404 belongs.
    """
    warrior = WarriorFactory(faction=current_savegame.player_faction)

    response = logged_in_client.get(
        reverse("warband:warrior-partial-update-view", kwargs={"pk": warrior.pk, "htmx_attribute": "name"})
    )

    assert response.status_code == 404


@pytest.mark.django_db
def test_warrior_dismiss_view_sends_him_to_the_pub(logged_in_client, current_savegame):
    """
    The whole chain, because the pub, the ledger and the month log all hang off the event - and two
    of those handlers run behind the database blocker, which a direct handler call lifts.
    """
    warrior = WarriorFactory(faction=current_savegame.player_faction, monthly_salary=120)
    TransactionFactory(faction=current_savegame.player_faction, amount=1000)

    response = logged_in_client.post(reverse("warband:warrior-dismiss-view", kwargs={"pk": warrior.id}))

    assert response.status_code == 200
    assert "HX-Trigger" in response.headers
    warrior.refresh_from_db()
    assert warrior.faction is None
    assert list(current_savegame.player_faction.available_mercenaries.all()) == [warrior]
    assert Transaction.objects.current_balance(faction_id=current_savegame.player_faction_id) == 880


@pytest.mark.django_db
def test_warrior_dismiss_view_leaves_his_gear_on_the_shelf(logged_in_client, current_savegame):
    """
    The silver the player raises by selling it is the point, and unoccupied is what
    "get_all_unoccupied_items" needs to see before the faction page will offer it.
    """
    weapon = ItemFactory(
        type=ItemType.objects.get(name="Short sword"),
        owner=current_savegame.player_faction,
        savegame=current_savegame,
    )
    warrior = WarriorFactory(faction=current_savegame.player_faction, weapon=weapon)
    TransactionFactory(faction=current_savegame.player_faction, amount=1000)

    response = logged_in_client.post(reverse("warband:warrior-dismiss-view", kwargs={"pk": warrior.id}))

    assert response.status_code == 200
    assert list(current_savegame.player_faction.get_all_unoccupied_items()) == [weapon]


@pytest.mark.django_db
def test_warrior_dismiss_view_refuses_the_leader(logged_in_client, current_savegame):
    """
    A refusal here means the page was stale rather than that the card and the view disagree - the
    control is not offered for him in the first place.
    """
    leader = WarriorFactory(faction=current_savegame.player_faction)
    current_savegame.player_faction.leader = leader
    current_savegame.player_faction.save()
    TransactionFactory(faction=current_savegame.player_faction, amount=1000)

    response = logged_in_client.post(reverse("warband:warrior-dismiss-view", kwargs={"pk": leader.id}))

    assert response.status_code == 204
    leader.refresh_from_db()
    assert leader.faction == current_savegame.player_faction


@pytest.mark.django_db
def test_warrior_dismiss_view_refuses_a_purse_that_cannot_pay_him_off(logged_in_client, current_savegame):
    warrior = WarriorFactory(faction=current_savegame.player_faction, monthly_salary=120)

    response = logged_in_client.post(reverse("warband:warrior-dismiss-view", kwargs={"pk": warrior.id}))

    assert response.status_code == 204
    warrior.refresh_from_db()
    assert warrior.faction == current_savegame.player_faction


@pytest.mark.django_db
def test_warrior_dismiss_view_cannot_empty_a_rivals_war_band(logged_in_client, current_savegame):
    """
    A rival's men are in the player's savegame too, so the savegame is not scope enough: the id from
    the URL was all it would take to shrink a rival's roster for him.
    """
    rival_faction = FactionFactory(savegame=current_savegame)
    rival_warrior = WarriorFactory(faction=rival_faction, savegame=current_savegame)
    TransactionFactory(faction=current_savegame.player_faction, amount=1000)

    response = logged_in_client.post(reverse("warband:warrior-dismiss-view", kwargs={"pk": rival_warrior.id}))

    assert response.status_code == 404
    rival_warrior.refresh_from_db()
    assert rival_warrior.faction == rival_faction


@pytest.mark.django_db
def test_warrior_dismiss_view_refuses_a_dead_warrior(logged_in_client, current_savegame):
    """
    Death leaves a man on the roster but off the page, he draws no wages, and there is nothing about
    him for a dismissal to fix - so he is narrowed away rather than refused with a sentence.
    """
    dead_warrior = WarriorFactory(
        faction=current_savegame.player_faction, condition=Warrior.ConditionChoices.CONDITION_DEAD
    )
    TransactionFactory(faction=current_savegame.player_faction, amount=1000)

    response = logged_in_client.post(reverse("warband:warrior-dismiss-view", kwargs={"pk": dead_warrior.id}))

    assert response.status_code == 404
    dead_warrior.refresh_from_db()
    assert dead_warrior.faction == current_savegame.player_faction
