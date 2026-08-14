import pytest
from django.urls import reverse

from apps.faction.tests.factories.faction import FactionFactory
from apps.skirmish.choices.skirmish_action import SkirmishActionChoices
from apps.skirmish.tests.factories.battle_history import BattleHistoryFactory
from apps.skirmish.tests.factories.skirmish import SkirmishFactory
from apps.skirmish.tests.factories.warrior import WarriorFactory


@pytest.mark.django_db
def test_skirmish_list_view_lists_the_skirmishes_of_the_current_savegame(logged_in_client, current_savegame):
    skirmish = SkirmishFactory(attacking_faction=current_savegame.player_faction)

    response = logged_in_client.get(reverse("skirmish:skirmish-list-view"))

    assert response.status_code == 200
    assert list(response.context["skirmish_list"]) == [skirmish]


@pytest.mark.django_db
def test_skirmish_list_view_hides_a_skirmish_of_another_savegame(logged_in_client, current_savegame):
    SkirmishFactory()

    response = logged_in_client.get(reverse("skirmish:skirmish-list-view"))

    assert response.status_code == 200
    assert list(response.context["skirmish_list"]) == []


@pytest.mark.django_db
def test_skirmish_fight_view_shows_the_skirmish(logged_in_client, current_savegame):
    skirmish = SkirmishFactory(attacking_faction=current_savegame.player_faction)

    response = logged_in_client.get(reverse("skirmish:skirmish-fight-view", kwargs={"pk": skirmish.pk}))

    assert response.status_code == 200
    assert response.context["object"] == skirmish


@pytest.mark.django_db
def test_skirmish_fight_view_marks_the_player_who_marched(logged_in_client, current_savegame):
    """
    The two flags drive whether a side's warrior cards offer the human a skirmish action, so exactly
    one of them may be True - here the player is the faction that marched.
    """
    skirmish = SkirmishFactory(attacking_faction=current_savegame.player_faction)

    response = logged_in_client.get(reverse("skirmish:skirmish-fight-view", kwargs={"pk": skirmish.pk}))

    assert response.context["attacker_is_player"] is True
    assert response.context["defender_is_player"] is False


@pytest.mark.django_db
def test_skirmish_fight_view_marks_the_player_who_was_marched_against(logged_in_client, current_savegame):
    """
    The player holds the defending side here, which is what makes the flags worth asserting: reading
    them off side one would hand the human the rival's warband and let the AI command his own.
    """
    skirmish = SkirmishFactory(
        attacking_faction=FactionFactory(savegame=current_savegame),
        defending_faction=current_savegame.player_faction,
    )

    response = logged_in_client.get(reverse("skirmish:skirmish-fight-view", kwargs={"pk": skirmish.pk}))

    assert response.context["attacker_is_player"] is False
    assert response.context["defender_is_player"] is True


@pytest.mark.django_db
def test_skirmish_fight_view_cannot_show_a_skirmish_of_another_savegame(logged_in_client, current_savegame):
    other_skirmish = SkirmishFactory()

    response = logged_in_client.get(reverse("skirmish:skirmish-fight-view", kwargs={"pk": other_skirmish.pk}))

    assert response.status_code == 404


@pytest.mark.django_db
def test_skirmish_fight_view_sends_the_player_back_with_another_skirmish_running(logged_in_client, current_savegame):
    skirmish = SkirmishFactory(attacking_faction=current_savegame.player_faction)
    SkirmishFactory(attacking_faction=current_savegame.player_faction, current_round=2)

    response = logged_in_client.get(reverse("skirmish:skirmish-fight-view", kwargs={"pk": skirmish.pk}))

    assert response.status_code == 302
    assert response.url == reverse("skirmish:skirmish-list-view")


@pytest.mark.django_db
def test_skirmish_finish_round_view_advances_the_round(logged_in_client, current_savegame):
    """
    Flow test: no mocking inside the chain, so this runs the real queue and asserts the end state.

    Combat itself is random, but a single round cannot decide the skirmish here: the fallback weapon
    deals at most 3 damage against 20 health, so both warriors stay healthy and only the round
    counter settles.
    """
    skirmish = SkirmishFactory(attacking_faction=current_savegame.player_faction)
    player_warrior = WarriorFactory(faction=skirmish.attacking_faction)
    opposing_warrior = WarriorFactory(faction=skirmish.defending_faction)
    skirmish.attacking_warriors.add(player_warrior)
    skirmish.defending_warriors.add(opposing_warrior)

    response = logged_in_client.post(
        reverse("skirmish:skirmish-finish-round-view", kwargs={"pk": skirmish.pk}),
        data={
            "skirmish_participant[0][faction_id]": skirmish.attacking_faction_id,
            "skirmish_participant[0][warrior_id]": player_warrior.pk,
            "skirmish_participant[0][skirmish_action]": SkirmishActionChoices.SIMPLE_ATTACK,
            "skirmish_participant[1][faction_id]": skirmish.defending_faction_id,
            "skirmish_participant[1][warrior_id]": opposing_warrior.pk,
            "skirmish_participant[1][skirmish_action]": SkirmishActionChoices.SIMPLE_ATTACK,
        },
    )

    assert response.status_code == 200
    assert "HX-Trigger" in response
    skirmish.refresh_from_db()
    assert skirmish.current_round == 2


@pytest.mark.django_db
def test_skirmish_finish_round_view_cannot_finish_a_round_of_another_savegame(logged_in_client, current_savegame):
    other_skirmish = SkirmishFactory()
    other_player_warrior = WarriorFactory(faction=other_skirmish.attacking_faction)
    other_opposing_warrior = WarriorFactory(faction=other_skirmish.defending_faction)
    other_skirmish.attacking_warriors.add(other_player_warrior)
    other_skirmish.defending_warriors.add(other_opposing_warrior)

    response = logged_in_client.post(
        reverse("skirmish:skirmish-finish-round-view", kwargs={"pk": other_skirmish.pk}),
        data={
            "skirmish_participant[0][faction_id]": other_skirmish.attacking_faction_id,
            "skirmish_participant[0][warrior_id]": other_player_warrior.pk,
            "skirmish_participant[0][skirmish_action]": SkirmishActionChoices.SIMPLE_ATTACK,
            "skirmish_participant[1][faction_id]": other_skirmish.defending_faction_id,
            "skirmish_participant[1][warrior_id]": other_opposing_warrior.pk,
            "skirmish_participant[1][skirmish_action]": SkirmishActionChoices.SIMPLE_ATTACK,
        },
    )

    assert response.status_code == 404
    other_skirmish.refresh_from_db()
    assert other_skirmish.current_round == 1


@pytest.mark.django_db
def test_skirmish_finish_round_view_takes_the_sides_from_the_roster_not_the_posted_faction(
    logged_in_client, current_savegame
):
    """
    "faction_id" is client-supplied. Naming the player's faction for an enemy warrior used to put
    that warrior into the player's line-up, where it attacked its own side; the rosters of the
    skirmish decide instead, so the round runs as a normal two-sided one.
    """
    skirmish = SkirmishFactory(attacking_faction=current_savegame.player_faction)
    player_warrior = WarriorFactory(faction=skirmish.attacking_faction)
    opposing_warrior = WarriorFactory(faction=skirmish.defending_faction)
    skirmish.attacking_warriors.add(player_warrior)
    skirmish.defending_warriors.add(opposing_warrior)

    response = logged_in_client.post(
        reverse("skirmish:skirmish-finish-round-view", kwargs={"pk": skirmish.pk}),
        data={
            "skirmish_participant[0][faction_id]": skirmish.attacking_faction_id,
            "skirmish_participant[0][warrior_id]": player_warrior.pk,
            "skirmish_participant[0][skirmish_action]": SkirmishActionChoices.SIMPLE_ATTACK,
            # Lying about the side of the enemy warrior
            "skirmish_participant[1][faction_id]": skirmish.attacking_faction_id,
            "skirmish_participant[1][warrior_id]": opposing_warrior.pk,
            "skirmish_participant[1][skirmish_action]": SkirmishActionChoices.SIMPLE_ATTACK,
        },
    )

    assert response.status_code == 200
    skirmish.refresh_from_db()
    assert skirmish.current_round == 2


@pytest.mark.django_db
def test_skirmish_finish_round_view_rejects_a_warrior_outside_the_skirmish(logged_in_client, current_savegame):
    """
    The warrior ids arrive in the request body, so one naming somebody who is not fighting this
    skirmish is bad input rather than a server error.
    """
    skirmish = SkirmishFactory(attacking_faction=current_savegame.player_faction)
    player_warrior = WarriorFactory(faction=skirmish.attacking_faction)
    skirmish.attacking_warriors.add(player_warrior)
    uninvolved_faction = FactionFactory(savegame=current_savegame)
    uninvolved_warrior = WarriorFactory(faction=uninvolved_faction)

    response = logged_in_client.post(
        reverse("skirmish:skirmish-finish-round-view", kwargs={"pk": skirmish.pk}),
        data={
            "skirmish_participant[0][faction_id]": skirmish.attacking_faction_id,
            "skirmish_participant[0][warrior_id]": player_warrior.pk,
            "skirmish_participant[0][skirmish_action]": SkirmishActionChoices.SIMPLE_ATTACK,
            "skirmish_participant[1][faction_id]": uninvolved_faction.pk,
            "skirmish_participant[1][warrior_id]": uninvolved_warrior.pk,
            "skirmish_participant[1][skirmish_action]": SkirmishActionChoices.SIMPLE_ATTACK,
        },
    )

    assert response.status_code == 400
    skirmish.refresh_from_db()
    assert skirmish.current_round == 1


@pytest.mark.django_db
def test_skirmish_finish_round_view_rejects_a_non_numeric_action(logged_in_client, current_savegame):
    skirmish = SkirmishFactory(attacking_faction=current_savegame.player_faction)
    player_warrior = WarriorFactory(faction=skirmish.attacking_faction)
    skirmish.attacking_warriors.add(player_warrior)

    response = logged_in_client.post(
        reverse("skirmish:skirmish-finish-round-view", kwargs={"pk": skirmish.pk}),
        data={
            "skirmish_participant[0][faction_id]": skirmish.attacking_faction_id,
            "skirmish_participant[0][warrior_id]": player_warrior.pk,
            "skirmish_participant[0][skirmish_action]": "charge",
        },
    )

    assert response.status_code == 400
    skirmish.refresh_from_db()
    assert skirmish.current_round == 1


@pytest.mark.django_db
def test_skirmish_finish_round_view_rejects_a_non_numeric_participant_index(logged_in_client, current_savegame):
    """
    The participant index is part of the field name, so it is request body too. Parsing happens
    before the view validates anything, so a hand-crafted index used to raise instead of answering.
    """
    skirmish = SkirmishFactory(attacking_faction=current_savegame.player_faction)
    player_warrior = WarriorFactory(faction=skirmish.attacking_faction)
    skirmish.attacking_warriors.add(player_warrior)

    response = logged_in_client.post(
        reverse("skirmish:skirmish-finish-round-view", kwargs={"pk": skirmish.pk}),
        data={
            "skirmish_participant[abc][warrior_id]": player_warrior.pk,
            "skirmish_participant[abc][skirmish_action]": SkirmishActionChoices.SIMPLE_ATTACK,
        },
    )

    assert response.status_code == 400
    skirmish.refresh_from_db()
    assert skirmish.current_round == 1


@pytest.mark.django_db
def test_skirmish_finish_round_view_rejects_a_participant_without_a_warrior_id(logged_in_client, current_savegame):
    skirmish = SkirmishFactory(attacking_faction=current_savegame.player_faction)
    player_warrior = WarriorFactory(faction=skirmish.attacking_faction)
    skirmish.attacking_warriors.add(player_warrior)

    response = logged_in_client.post(
        reverse("skirmish:skirmish-finish-round-view", kwargs={"pk": skirmish.pk}),
        data={
            "skirmish_participant[0][faction_id]": skirmish.attacking_faction_id,
            "skirmish_participant[0][skirmish_action]": SkirmishActionChoices.SIMPLE_ATTACK,
        },
    )

    assert response.status_code == 400
    skirmish.refresh_from_db()
    assert skirmish.current_round == 1


@pytest.mark.django_db
def test_skirmish_finish_round_view_refuses_a_one_sided_round(logged_in_client, current_savegame):
    skirmish = SkirmishFactory(attacking_faction=current_savegame.player_faction)
    player_warrior = WarriorFactory(faction=skirmish.attacking_faction)
    skirmish.attacking_warriors.add(player_warrior)

    response = logged_in_client.post(
        reverse("skirmish:skirmish-finish-round-view", kwargs={"pk": skirmish.pk}),
        data={
            "skirmish_participant[0][faction_id]": skirmish.attacking_faction_id,
            "skirmish_participant[0][warrior_id]": player_warrior.pk,
            "skirmish_participant[0][skirmish_action]": SkirmishActionChoices.SIMPLE_ATTACK,
        },
    )

    assert response.status_code == 400
    skirmish.refresh_from_db()
    assert skirmish.current_round == 1


@pytest.mark.django_db
def test_skirmish_round_update_htmx_view_shows_the_skirmish(logged_in_client, current_savegame):
    skirmish = SkirmishFactory(attacking_faction=current_savegame.player_faction)

    response = logged_in_client.get(reverse("skirmish:skirmish-round-update-htmx", kwargs={"pk": skirmish.pk}))

    assert response.status_code == 200
    assert response.context["object"] == skirmish


@pytest.mark.django_db
def test_skirmish_round_update_htmx_view_cannot_show_a_skirmish_of_another_savegame(logged_in_client, current_savegame):
    other_skirmish = SkirmishFactory()

    response = logged_in_client.get(reverse("skirmish:skirmish-round-update-htmx", kwargs={"pk": other_skirmish.pk}))

    assert response.status_code == 404


@pytest.mark.django_db
def test_skirmish_fight_button_update_htmx_view_shows_the_skirmish(logged_in_client, current_savegame):
    skirmish = SkirmishFactory(attacking_faction=current_savegame.player_faction)

    response = logged_in_client.get(reverse("skirmish:skirmish-fight-button-update-htmx", kwargs={"pk": skirmish.pk}))

    assert response.status_code == 200
    assert response.context["object"] == skirmish


@pytest.mark.django_db
def test_skirmish_fight_button_update_htmx_view_cannot_show_a_skirmish_of_another_savegame(
    logged_in_client, current_savegame
):
    other_skirmish = SkirmishFactory()

    response = logged_in_client.get(
        reverse("skirmish:skirmish-fight-button-update-htmx", kwargs={"pk": other_skirmish.pk})
    )

    assert response.status_code == 404


@pytest.mark.django_db
def test_battle_history_update_htmx_view_lists_the_history_of_the_skirmish(logged_in_client, current_savegame):
    skirmish = SkirmishFactory(attacking_faction=current_savegame.player_faction)
    battle_history = BattleHistoryFactory(skirmish=skirmish)

    response = logged_in_client.get(reverse("skirmish:battle-history-update-htmx", kwargs={"skirmish_id": skirmish.id}))

    assert response.status_code == 200
    assert list(response.context["battlehistory_list"]) == [battle_history]


@pytest.mark.django_db
def test_battle_history_update_htmx_view_hides_history_of_another_savegame(logged_in_client, current_savegame):
    other_skirmish = SkirmishFactory()
    BattleHistoryFactory(skirmish=other_skirmish)

    response = logged_in_client.get(
        reverse("skirmish:battle-history-update-htmx", kwargs={"skirmish_id": other_skirmish.id})
    )

    assert response.status_code == 200
    assert list(response.context["battlehistory_list"]) == []


@pytest.mark.django_db
def test_faction_warrior_list_update_htmx_view_lists_the_warriors_of_the_attacking_faction(
    logged_in_client, current_savegame
):
    skirmish = SkirmishFactory(attacking_faction=current_savegame.player_faction)
    player_warrior = WarriorFactory(faction=skirmish.attacking_faction)
    skirmish.attacking_warriors.add(player_warrior)

    response = logged_in_client.get(
        reverse(
            "skirmish:faction-warrior-list-update-htmx",
            kwargs={"skirmish_id": skirmish.pk, "faction_id": skirmish.attacking_faction_id},
        )
    )

    assert response.status_code == 200
    assert list(response.context["object_list"]) == [player_warrior]


@pytest.mark.django_db
def test_faction_warrior_list_update_htmx_view_lists_the_warriors_of_the_defending_faction(
    logged_in_client, current_savegame
):
    skirmish = SkirmishFactory(attacking_faction=current_savegame.player_faction)
    opposing_warrior = WarriorFactory(faction=skirmish.defending_faction)
    skirmish.defending_warriors.add(opposing_warrior)

    response = logged_in_client.get(
        reverse(
            "skirmish:faction-warrior-list-update-htmx",
            kwargs={"skirmish_id": skirmish.pk, "faction_id": skirmish.defending_faction_id},
        )
    )

    assert response.status_code == 200
    assert list(response.context["object_list"]) == [opposing_warrior]


@pytest.mark.django_db
def test_faction_warrior_list_update_htmx_view_marks_the_players_own_roster(logged_in_client, current_savegame):
    """
    The player holds the defending side, so the flag has to come from the savegame: taken from the
    attacking side it would call the player's own warband the enemy and stop him commanding it.
    """
    skirmish = SkirmishFactory(
        attacking_faction=FactionFactory(savegame=current_savegame),
        defending_faction=current_savegame.player_faction,
    )

    response = logged_in_client.get(
        reverse(
            "skirmish:faction-warrior-list-update-htmx",
            kwargs={"skirmish_id": skirmish.pk, "faction_id": skirmish.defending_faction_id},
        )
    )

    assert response.status_code == 200
    assert response.context["is_player"] is True


@pytest.mark.django_db
def test_faction_warrior_list_update_htmx_view_marks_a_rival_roster_as_not_the_players(
    logged_in_client, current_savegame
):
    """
    The mirror image: the rival marched, and being the attacker must not make its warband the human's
    to command.
    """
    skirmish = SkirmishFactory(
        attacking_faction=FactionFactory(savegame=current_savegame),
        defending_faction=current_savegame.player_faction,
    )

    response = logged_in_client.get(
        reverse(
            "skirmish:faction-warrior-list-update-htmx",
            kwargs={"skirmish_id": skirmish.pk, "faction_id": skirmish.attacking_faction_id},
        )
    )

    assert response.status_code == 200
    assert response.context["is_player"] is False


@pytest.mark.django_db
def test_faction_warrior_list_update_htmx_view_cannot_list_warriors_of_another_savegame(
    logged_in_client, current_savegame
):
    other_skirmish = SkirmishFactory()
    other_warrior = WarriorFactory(faction=other_skirmish.attacking_faction)
    other_skirmish.attacking_warriors.add(other_warrior)

    response = logged_in_client.get(
        reverse(
            "skirmish:faction-warrior-list-update-htmx",
            kwargs={"skirmish_id": other_skirmish.pk, "faction_id": other_skirmish.attacking_faction_id},
        )
    )

    assert response.status_code == 404
