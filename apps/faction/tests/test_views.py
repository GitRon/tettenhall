import json

import pytest
from django.contrib.messages import get_messages
from django.urls import reverse

from apps.faction.models.faction import Faction
from apps.faction.tests.factories.faction import FactionFactory
from apps.finance.models.transaction import Transaction
from apps.finance.tests.factories.transaction import TransactionFactory
from apps.item.models.item_type import ItemType
from apps.item.tests.factories.item import ItemFactory
from apps.item.tests.factories.item_type import ItemTypeFactory
from apps.quest.tests.factories.quest import QuestFactory
from apps.savegame.models.savegame import Savegame
from apps.savegame.tests.factories.savegame import SavegameFactory
from apps.skirmish.models.skirmish import Skirmish
from apps.skirmish.models.warrior import Warrior
from apps.skirmish.tests.factories.skirmish import SkirmishFactory
from apps.skirmish.tests.factories.warrior import WarriorFactory
from apps.town.buildings.hall import MediumHall
from apps.town.models import Town
from apps.training.tests.factories.training import TrainingFactory


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
    warrior = WarriorFactory(faction=faction)

    response = logged_in_client.get(reverse("faction:faction-detail-view", kwargs={"pk": faction.id}))

    assert response.status_code == 200
    assert list(response.context["warrior_list"]) == [warrior]


@pytest.mark.django_db
def test_faction_detail_view_hides_factions_of_other_savegames(logged_in_client, current_savegame):
    other_savegame = SavegameFactory()
    foreign_faction = FactionFactory(savegame=other_savegame)

    response = logged_in_client.get(reverse("faction:faction-detail-view", kwargs={"pk": foreign_faction.id}))

    assert response.status_code == 404


@pytest.mark.django_db
def test_faction_detail_view_marks_the_players_own_faction(logged_in_client, current_savegame):
    response = logged_in_client.get(
        reverse("faction:faction-detail-view", kwargs={"pk": current_savegame.player_faction.id})
    )

    assert response.status_code == 200
    assert response.context["is_player_faction"] is True


@pytest.mark.django_db
def test_faction_detail_view_does_not_mark_a_rival_as_the_players_own(logged_in_client, current_savegame):
    """
    The same template serves both, and on a rival's page "My faction" and the fyrd card offer a draft
    the scoping on DraftWarriorFromFyrdView can only refuse.
    """
    rival_faction = FactionFactory(savegame=current_savegame)

    response = logged_in_client.get(reverse("faction:faction-detail-view", kwargs={"pk": rival_faction.id}))

    assert response.status_code == 200
    assert response.context["is_player_faction"] is False


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
    # A rival he has not touched: its own men are free, so his march is the only thing in the way
    untouched_rival = FactionFactory(savegame=current_savegame)
    WarriorFactory(faction=untouched_rival)
    skirmish = SkirmishFactory(
        attacking_faction=player_faction_ready_to_march,
        defending_faction=FactionFactory(savegame=current_savegame),
        victorious_faction=player_faction_ready_to_march,
        month=current_savegame.current_month,
    )
    skirmish.attacking_warriors.add(player_faction_ready_to_march.leader)

    response = logged_in_client.get(reverse("faction:faction-detail-view", kwargs={"pk": untouched_rival.id}))

    assert response.context["can_be_attacked"] is False
    assert response.context["has_marched_this_month"] is True


@pytest.mark.django_db
def test_faction_detail_view_says_why_the_attack_is_gone_on_the_rival_he_marched_on(
    logged_in_client, current_savegame, player_faction_ready_to_march
):
    """
    The page he is most likely to be looking at, and the one that went quiet: a real march puts the
    target's defenders on the skirmish roster too, which takes the faction out of "attackable_targets"
    and used to take the sentence with it.
    """
    rival_faction = FactionFactory(savegame=current_savegame)
    rival_warrior = WarriorFactory(faction=rival_faction)
    skirmish = SkirmishFactory(
        attacking_faction=player_faction_ready_to_march,
        defending_faction=rival_faction,
        victorious_faction=player_faction_ready_to_march,
        month=current_savegame.current_month,
    )
    skirmish.attacking_warriors.add(player_faction_ready_to_march.leader)
    skirmish.defending_warriors.add(rival_warrior)

    response = logged_in_client.get(reverse("faction:faction-detail-view", kwargs={"pk": rival_faction.id}))

    assert response.context["can_be_attacked"] is False
    assert response.context["has_marched_this_month"] is True


@pytest.mark.django_db
def test_faction_detail_view_says_when_the_rivals_own_war_band_is_committed(
    logged_in_client, current_savegame, player_faction_ready_to_march
):
    """
    The other side of "every warrior fights once a month". His war band is free - he has not marched -
    but theirs is spoken for, which a quest accepted against them does as surely as a fight does.
    """
    rival_faction = FactionFactory(savegame=current_savegame)
    committed_defender = WarriorFactory(faction=rival_faction)
    SkirmishFactory(defending_faction=rival_faction).defending_warriors.add(committed_defender)

    response = logged_in_client.get(reverse("faction:faction-detail-view", kwargs={"pk": rival_faction.id}))

    assert response.context["has_marched_this_month"] is False
    assert response.context["their_war_band_is_committed"] is True


@pytest.mark.django_db
def test_faction_detail_view_says_nothing_about_a_committed_war_band_on_a_defeated_faction(
    logged_in_client, current_savegame, player_faction_ready_to_march
):
    """
    A knocked-out faction never offered a fight, so neither sentence applies - the same reason the
    marching one stays quiet there.
    """
    defeated_faction = FactionFactory(savegame=current_savegame, is_defeated=True)
    WarriorFactory(faction=defeated_faction)

    response = logged_in_client.get(reverse("faction:faction-detail-view", kwargs={"pk": defeated_faction.id}))

    assert response.context["can_be_attacked"] is False
    assert response.context["their_war_band_is_committed"] is False


@pytest.mark.django_db
def test_faction_detail_view_says_nothing_about_marching_on_the_players_own_faction(
    logged_in_client, current_savegame, player_faction_ready_to_march
):
    """
    You can never march on yourself, so "your warriors have already fought" is not the reason the
    button is missing - it was never on offer.
    """
    skirmish = SkirmishFactory(
        attacking_faction=player_faction_ready_to_march,
        defending_faction=FactionFactory(savegame=current_savegame),
        victorious_faction=player_faction_ready_to_march,
        month=current_savegame.current_month,
    )
    skirmish.attacking_warriors.add(player_faction_ready_to_march.leader)

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
        attacking_faction=player_faction_ready_to_march,
        defending_faction=defeated_faction,
        victorious_faction=player_faction_ready_to_march,
        month=current_savegame.current_month,
    )
    skirmish.attacking_warriors.add(player_faction_ready_to_march.leader)

    response = logged_in_client.get(reverse("faction:faction-detail-view", kwargs={"pk": defeated_faction.id}))

    assert response.context["can_be_attacked"] is False
    assert response.context["has_marched_this_month"] is False


@pytest.mark.django_db
def test_rival_faction_list_view_lists_the_rivals_with_their_roster(logged_in_client, current_savegame):
    rival_faction = FactionFactory(savegame=current_savegame)
    WarriorFactory(faction=rival_faction)
    WarriorFactory(faction=rival_faction, condition=Warrior.ConditionChoices.CONDITION_DEAD)

    response = logged_in_client.get(reverse("faction:rival-faction-list-view"))

    assert list(response.context["rival_list"]) == [rival_faction]
    assert response.context["rival_list"][0].warrior_count == 1


@pytest.mark.django_db
def test_rival_faction_list_view_excludes_a_defeated_rival(logged_in_client, current_savegame):
    """
    The same queryset that decides who is still on the board, so a knocked-out rival drops off this
    page for the same reason it stops getting a month.
    """
    FactionFactory(savegame=current_savegame, is_defeated=True)

    response = logged_in_client.get(reverse("faction:rival-faction-list-view"))

    assert list(response.context["rival_list"]) == []


@pytest.mark.django_db
def test_rival_faction_list_view_hides_factions_of_other_savegames(logged_in_client, current_savegame):
    other_savegame = SavegameFactory()
    FactionFactory(savegame=other_savegame)

    response = logged_in_client.get(reverse("faction:rival-faction-list-view"))

    assert list(response.context["rival_list"]) == []


@pytest.mark.django_db
def test_rival_faction_list_view_without_a_player_faction(logged_in_client, savegame_without_player_faction):
    """
    Who counts as a rival is a question about the player's own faction, so before there is one there
    is nobody to list - not a server error.
    """
    FactionFactory(savegame=savegame_without_player_faction)

    response = logged_in_client.get(reverse("faction:rival-faction-list-view"))

    assert response.status_code == 200
    assert list(response.context["rival_list"]) == []


@pytest.mark.django_db
def test_rival_faction_list_view_offers_an_attack_on_a_rival(
    logged_in_client, current_savegame, player_faction_ready_to_march
):
    rival_faction = FactionFactory(savegame=current_savegame)
    WarriorFactory(faction=rival_faction)

    response = logged_in_client.get(reverse("faction:rival-faction-list-view"))

    assert response.context["rival_list"][0].can_be_attacked is True


@pytest.mark.django_db
def test_rival_faction_list_view_says_when_a_rivals_own_war_band_is_committed(
    logged_in_client, current_savegame, player_faction_ready_to_march
):
    """
    His war band is free but theirs is spoken for, so the missing button is the rival's doing - said
    per row, because it is the one of the three reasons that is about a single rival.
    """
    rival_faction = FactionFactory(savegame=current_savegame)
    committed_defender = WarriorFactory(faction=rival_faction)
    SkirmishFactory(defending_faction=rival_faction).defending_warriors.add(committed_defender)

    response = logged_in_client.get(reverse("faction:rival-faction-list-view"))

    assert response.context["rival_list"][0].can_be_attacked is False
    assert response.context["rival_list"][0].their_war_band_is_committed is True


@pytest.mark.django_db
def test_rival_faction_list_view_says_the_war_band_has_already_marched(
    logged_in_client, current_savegame, player_faction_ready_to_march
):
    """
    A fact about the player's own war band rather than about any one rival, so it is said once for the
    whole page instead of on every row.
    """
    untouched_rival = FactionFactory(savegame=current_savegame)
    WarriorFactory(faction=untouched_rival)
    skirmish = SkirmishFactory(
        attacking_faction=player_faction_ready_to_march,
        defending_faction=FactionFactory(savegame=current_savegame),
        victorious_faction=player_faction_ready_to_march,
        month=current_savegame.current_month,
    )
    skirmish.attacking_warriors.add(player_faction_ready_to_march.leader)

    response = logged_in_client.get(reverse("faction:rival-faction-list-view"))

    assert response.context["has_marched_this_month"] is True
    assert response.context["leader_cannot_march"] is False


@pytest.mark.django_db
def test_rival_faction_list_view_says_the_leader_cannot_march(logged_in_client, current_savegame):
    """
    Nothing is keeping the war band busy, so the reason is the leader himself - here a faction that
    has none at all, which is what a captured or killed leader leaves behind.
    """
    rival_faction = FactionFactory(savegame=current_savegame)
    WarriorFactory(faction=rival_faction)

    response = logged_in_client.get(reverse("faction:rival-faction-list-view"))

    assert response.context["has_marched_this_month"] is False
    assert response.context["leader_cannot_march"] is True


@pytest.mark.django_db
def test_rival_faction_list_view_stays_quiet_over_an_empty_board(logged_in_client, current_savegame):
    """
    No rival is standing, so there is no missing button to explain: the sentences would be about a
    fight nothing was ever going to offer.
    """
    FactionFactory(savegame=current_savegame, is_defeated=True)

    response = logged_in_client.get(reverse("faction:rival-faction-list-view"))

    assert response.context["has_marched_this_month"] is False
    assert response.context["leader_cannot_march"] is False


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
    # A levy called up out of the fyrd costs nothing, and a ledger row reading "-0 silver" is not a
    # payment - every faction drafts every month it can, so those rows would bury the real ones
    assert Transaction.objects.filter(faction=faction).exists() is False


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


@pytest.fixture
def pub_mercenary(current_savegame) -> Warrior:
    """
    A mercenary standing in the player's pub, priced at 180 silver.

    Unhired stock has no faction of its own, so the factory cannot reach through one for the savegame
    and the culture the way it does everywhere else.
    """
    faction = current_savegame.player_faction
    mercenary = WarriorFactory(
        faction=None,
        savegame=current_savegame,
        culture=faction.culture,
        recruitment_price=180,
    )
    faction.available_mercenaries.add(mercenary)

    return mercenary


@pytest.mark.django_db
def test_recruit_pub_mercenary_view_hires_him(logged_in_client, current_savegame, pub_mercenary, queuebie_registry):
    """
    Flow test: no mocking inside the chain, so this runs the real queue and asserts the end state.
    """
    TransactionFactory(faction=current_savegame.player_faction, amount=500)

    response = logged_in_client.post(reverse("faction:pub-mercenary-recruit-view", kwargs={"pk": pub_mercenary.id}))

    assert response.status_code == 200
    pub_mercenary.refresh_from_db()
    assert pub_mercenary.faction == current_savegame.player_faction


@pytest.mark.django_db
def test_recruit_pub_mercenary_view_debits_his_price(
    logged_in_client, current_savegame, pub_mercenary, queuebie_registry
):
    TransactionFactory(faction=current_savegame.player_faction, amount=500)

    response = logged_in_client.post(reverse("faction:pub-mercenary-recruit-view", kwargs={"pk": pub_mercenary.id}))

    assert "HX-Trigger" in response.headers
    assert Transaction.objects.filter(faction=current_savegame.player_faction, amount=-180).exists() is True


@pytest.mark.django_db
def test_recruit_pub_mercenary_view_takes_him_off_the_pub_shelf(
    logged_in_client, current_savegame, pub_mercenary, queuebie_registry
):
    TransactionFactory(faction=current_savegame.player_faction, amount=500)

    response = logged_in_client.post(reverse("faction:pub-mercenary-recruit-view", kwargs={"pk": pub_mercenary.id}))

    assert response.status_code == 200
    assert list(current_savegame.player_faction.available_mercenaries.all()) == []


@pytest.mark.django_db
def test_recruit_pub_mercenary_view_hands_his_gear_to_the_faction(
    logged_in_client, current_savegame, pub_mercenary, queuebie_registry
):
    """
    Pub gear is generated unowned, and an unowned item never reaches "get_all_unoccupied_items" - the
    faction could neither re-equip nor sell what it has just paid for.
    """
    TransactionFactory(faction=current_savegame.player_faction, amount=500)
    weapon = ItemFactory(
        type=ItemTypeFactory(function=ItemType.FunctionChoices.FUNCTION_WEAPON),
        savegame=current_savegame,
        owner=None,
    )
    pub_mercenary.weapon = weapon
    pub_mercenary.save()

    response = logged_in_client.post(reverse("faction:pub-mercenary-recruit-view", kwargs={"pk": pub_mercenary.id}))

    assert response.status_code == 200
    weapon.refresh_from_db()
    assert weapon.owner == current_savegame.player_faction


@pytest.mark.django_db
def test_recruit_pub_mercenary_view_refuses_without_enough_silver(
    logged_in_client, current_savegame, pub_mercenary, queuebie_registry
):
    TransactionFactory(faction=current_savegame.player_faction, amount=50)

    response = logged_in_client.post(reverse("faction:pub-mercenary-recruit-view", kwargs={"pk": pub_mercenary.id}))

    assert response.status_code == 204
    assert json.loads(response["HX-Trigger"]) == {
        "notification": "You don't have enough silver to hire this mercenary."
    }
    pub_mercenary.refresh_from_db()
    assert pub_mercenary.faction is None


@pytest.mark.django_db
def test_recruit_pub_mercenary_view_cannot_hire_the_same_man_twice(
    logged_in_client, current_savegame, pub_mercenary, queuebie_registry
):
    """
    He leaves the pub when he is hired, and the scoping resolves nothing outside it - so a second
    post cannot buy the same man again.
    """
    TransactionFactory(faction=current_savegame.player_faction, amount=500)
    logged_in_client.post(reverse("faction:pub-mercenary-recruit-view", kwargs={"pk": pub_mercenary.id}))

    response = logged_in_client.post(reverse("faction:pub-mercenary-recruit-view", kwargs={"pk": pub_mercenary.id}))

    assert response.status_code == 404
    assert Transaction.objects.filter(faction=current_savegame.player_faction, amount=-180).count() == 1


@pytest.mark.django_db
def test_recruit_pub_mercenary_view_hides_the_pub_of_another_savegame(
    logged_in_client, current_savegame, queuebie_registry
):
    TransactionFactory(faction=current_savegame.player_faction, amount=500)
    other_savegame = SavegameFactory()
    other_faction = FactionFactory(savegame=other_savegame)
    other_mercenary = WarriorFactory(
        faction=None, savegame=other_savegame, culture=other_faction.culture, recruitment_price=180
    )
    other_faction.available_mercenaries.add(other_mercenary)

    response = logged_in_client.post(reverse("faction:pub-mercenary-recruit-view", kwargs={"pk": other_mercenary.id}))

    assert response.status_code == 404
    other_mercenary.refresh_from_db()
    assert other_mercenary.faction is None


@pytest.mark.django_db
def test_recruit_pub_mercenary_view_cannot_hire_a_warrior_outside_the_pub(
    logged_in_client, current_savegame, queuebie_registry
):
    """
    Being in the savegame is not enough: rival warriors, captives and deserters are all "Warrior"
    rows, and the price check alone would hand most of them over for nothing.
    """
    TransactionFactory(faction=current_savegame.player_faction, amount=500)
    rival_faction = FactionFactory(savegame=current_savegame)
    rival_warrior = WarriorFactory(faction=rival_faction, recruitment_price=180)

    response = logged_in_client.post(reverse("faction:pub-mercenary-recruit-view", kwargs={"pk": rival_warrior.id}))

    assert response.status_code == 404
    rival_warrior.refresh_from_db()
    assert rival_warrior.faction == rival_faction


@pytest.mark.django_db
def test_recruit_pub_mercenary_view_without_a_player_faction(
    logged_in_client, savegame_without_player_faction, queuebie_registry
):
    """
    There is no own faction to hire into yet, so the scoping narrows to nothing.
    """
    faction = FactionFactory(savegame=savegame_without_player_faction)
    mercenary = WarriorFactory(
        faction=None, savegame=savegame_without_player_faction, culture=faction.culture, recruitment_price=180
    )
    faction.available_mercenaries.add(mercenary)

    response = logged_in_client.post(reverse("faction:pub-mercenary-recruit-view", kwargs={"pk": mercenary.id}))

    assert response.status_code == 404
    mercenary.refresh_from_db()
    assert mercenary.faction is None


@pytest.mark.django_db
def test_recruit_pub_mercenary_view_keeps_him_through_the_monthly_restock(
    logged_in_client, current_savegame, pub_mercenary, queuebie_registry
):
    """
    Flow test across a month boundary, which is the only level this trap is visible at.

    "handle_restock_pub_mercenaries" clears the stock with "available_mercenaries.all().delete()" -
    a warrior queryset, so it deletes the rows themselves. A hired man still linked to the pub is
    therefore deleted at the start of the next month, after he has been paid for and equipped.
    """
    TransactionFactory(faction=current_savegame.player_faction, amount=500)
    # The month chain trains the current training and restocks the bulletin board, and a quest needs
    # somebody to target
    TrainingFactory(faction=current_savegame.player_faction)
    FactionFactory(savegame=current_savegame)
    logged_in_client.post(reverse("faction:pub-mercenary-recruit-view", kwargs={"pk": pub_mercenary.id}))

    response = logged_in_client.post(reverse("month:finish-month-view"))

    assert response.status_code == 200
    assert Warrior.objects.filter(id=pub_mercenary.id, faction=current_savegame.player_faction).exists() is True


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
    skirmish = Skirmish.objects.get(defending_faction=rival_faction)
    assert list(skirmish.defending_warriors.all()) == [rival_leader]
    assert list(skirmish.attacking_warriors.all()) == [player_faction_ready_to_march.leader, follower]
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
        attacking_faction=player_faction_ready_to_march,
        defending_faction=already_fought,
        victorious_faction=player_faction_ready_to_march,
        month=current_savegame.current_month,
    )
    fought_skirmish.attacking_warriors.add(player_faction_ready_to_march.leader)
    untouched_rival = FactionFactory(savegame=current_savegame)
    WarriorFactory(faction=untouched_rival)

    response = logged_in_client.post(reverse("faction:faction-attack-view", kwargs={"pk": untouched_rival.id}), data={})

    assert response.status_code == 404
    assert Skirmish.objects.count() == 1


@pytest.mark.django_db
def test_faction_attack_view_sends_the_player_home_on_a_finished_savegame(
    logged_in_client, current_savegame, player_faction_ready_to_march
):
    """
    A decided savegame has to read as "this game is over", not as a 404 about a rival that is no
    longer on offer. Resolving the target in the view's own dispatch used to answer first and hide
    the guard entirely - a browser walkthrough found it, since both refusals look the same from a
    test that only asserts "not 200".
    """
    rival_faction = FactionFactory(savegame=current_savegame)
    WarriorFactory(faction=rival_faction)
    current_savegame.outcome = Savegame.OutcomeChoices.OUTCOME_LOST
    current_savegame.save()

    response = logged_in_client.get(reverse("faction:faction-attack-view", kwargs={"pk": rival_faction.id}))

    assert response.status_code == 302
    assert response.url == reverse("account:dashboard-view")
    assert [str(message) for message in get_messages(response.wsgi_request)] == [
        "This game is over. Start a new savegame to play on."
    ]


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
    """
    The wage bill is not this view's own any more: it comes off "wage_bill_payroll", the projection
    the salary run bills from, so the card and the month cannot disagree about the number.
    """
    WarriorFactory(faction=current_savegame.player_faction, monthly_salary=30)
    WarriorFactory(faction=current_savegame.player_faction, monthly_salary=12)

    response = logged_in_client.get(
        reverse("faction:faction-monthly-costs-view", kwargs={"pk": current_savegame.player_faction.id})
    )

    assert response.status_code == 200
    assert response.context["wage_bill_payroll"].total_amount == 42


@pytest.mark.django_db
def test_monthly_cost_overview_names_the_income_of_the_hall(logged_in_client, current_savegame):
    """
    The one number the card assembles itself, because nothing else on any page shows it - off the
    town the same way the month reads it. A hall above the baseline, so a card answering with the
    default income for every town would fail here.
    """
    town = current_savegame.player_faction.town
    town.hall = Town.HallChoices.HALL_MEDIUM
    town.save()

    response = logged_in_client.get(
        reverse("faction:faction-monthly-costs-view", kwargs={"pk": current_savegame.player_faction.id})
    )

    assert response.status_code == 200
    assert response.context["building_income_amount"] == MediumHall.REVENUE_PER_ROUND


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
def test_town_square_view_offers_only_quests_that_can_still_be_taken_on(logged_in_client, current_savegame):
    """
    Scoped the same way QuestAcceptView resolves its quest, so the card and the page it leads to
    cannot disagree - the opposition is the target's own war band, and one the player has beaten inside
    this month fields nobody.
    """
    fightable_quest = QuestFactory(target_faction__savegame=current_savegame)
    WarriorFactory(faction=fightable_quest.target_faction)
    flattened_quest = QuestFactory(target_faction__savegame=current_savegame)
    WarriorFactory(faction=flattened_quest.target_faction, condition=Warrior.ConditionChoices.CONDITION_UNCONSCIOUS)
    current_savegame.player_faction.available_quests.add(fightable_quest, flattened_quest)

    response = logged_in_client.get(
        reverse("faction:town-square-view", kwargs={"pk": current_savegame.player_faction.id})
    )

    assert response.status_code == 200
    assert list(response.context["quest_list"]) == [fightable_quest]


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


@pytest.mark.django_db
def test_faction_detail_view_does_not_blame_the_rival_when_the_players_leader_cannot_march(
    logged_in_client, current_savegame
):
    """
    The sentence exists to explain the missing button, so it must not point at the rival when the
    player could not have marched on anybody. His leader is down here - not busy, so nothing says he
    has already fought - and the rival's men happen to be committed as well. Blaming them sends him
    off to wait for a month that will not give the button back.
    """
    player_faction = current_savegame.player_faction
    player_faction.leader = WarriorFactory(
        faction=player_faction, condition=Warrior.ConditionChoices.CONDITION_UNCONSCIOUS
    )
    player_faction.save()
    rival_faction = FactionFactory(savegame=current_savegame)
    committed_defender = WarriorFactory(faction=rival_faction)
    SkirmishFactory(defending_faction=rival_faction).defending_warriors.add(committed_defender)

    response = logged_in_client.get(reverse("faction:faction-detail-view", kwargs={"pk": rival_faction.id}))

    assert response.context["their_war_band_is_committed"] is False
    assert response.context["leader_cannot_march"] is True


@pytest.mark.django_db
def test_faction_detail_view_says_when_the_leader_is_in_no_condition_to_march(logged_in_client, current_savegame):
    """
    The third way the button goes: nothing is wrong with the rival and the war band has not fought, the
    leader is simply not fit to lead it. He joins every attack, so he is the whole of the refusal - and
    unlike the other two this one names something the player can act on.
    """
    player_faction = current_savegame.player_faction
    player_faction.leader = WarriorFactory(
        faction=player_faction, condition=Warrior.ConditionChoices.CONDITION_UNCONSCIOUS
    )
    player_faction.save()
    rival_faction = FactionFactory(savegame=current_savegame)
    WarriorFactory(faction=rival_faction)

    response = logged_in_client.get(reverse("faction:faction-detail-view", kwargs={"pk": rival_faction.id}))

    assert response.context["can_be_attacked"] is False
    assert response.context["leader_cannot_march"] is True


@pytest.mark.django_db
def test_faction_detail_view_blames_the_march_rather_than_the_leader_when_he_has_fought(
    logged_in_client, current_savegame, player_faction_ready_to_march
):
    """
    A leader who marched is unavailable too, so both sentences could claim him. The march is the more
    useful thing to say - it is true of every rival that month, not just this one.
    """
    rival_faction = FactionFactory(savegame=current_savegame)
    WarriorFactory(faction=rival_faction)
    skirmish = SkirmishFactory(
        attacking_faction=player_faction_ready_to_march,
        defending_faction=FactionFactory(savegame=current_savegame),
        victorious_faction=player_faction_ready_to_march,
        month=current_savegame.current_month,
    )
    skirmish.attacking_warriors.add(player_faction_ready_to_march.leader)

    response = logged_in_client.get(reverse("faction:faction-detail-view", kwargs={"pk": rival_faction.id}))

    assert response.context["has_marched_this_month"] is True
    assert response.context["leader_cannot_march"] is False


@pytest.fixture
def undefended_rival(current_savegame) -> Faction:
    """
    A rival whose last man on his feet has just gone down: a leader, and nobody healthy.

    The state a won battle leaves behind, and the only one an occupation can be launched from, so
    every case below opens from it.
    """
    rival = FactionFactory(savegame=current_savegame)
    rival.leader = WarriorFactory(faction=rival, condition=Warrior.ConditionChoices.CONDITION_UNCONSCIOUS)
    rival.save()

    return rival


@pytest.mark.django_db
def test_faction_detail_view_offers_an_undefended_town(logged_in_client, current_savegame, undefended_rival):
    response = logged_in_client.get(reverse("faction:faction-detail-view", kwargs={"pk": undefended_rival.id}))

    assert response.status_code == 200
    assert response.context["can_be_occupied"] is True


@pytest.mark.django_db
def test_rival_faction_list_view_offers_an_undefended_town(logged_in_client, current_savegame, undefended_rival):
    response = logged_in_client.get(reverse("faction:rival-faction-list-view"))

    assert response.status_code == 200
    assert [rival.can_be_occupied for rival in response.context["rival_list"]] == [True]


@pytest.mark.django_db
def test_faction_occupy_view_takes_the_town(logged_in_client, current_savegame, undefended_rival, queuebie_registry):
    """
    Flow test: no mocking inside the chain, so this runs the real queue and asserts the end state -
    the leader is a prisoner, the faction is knocked out and half the treasury has changed hands.
    """
    TransactionFactory(faction=undefended_rival, amount=800)

    response = logged_in_client.post(reverse("faction:faction-occupy-view", kwargs={"pk": undefended_rival.id}))

    assert response.status_code == 302
    undefended_rival.refresh_from_db()
    assert undefended_rival.is_defeated is True
    assert list(current_savegame.player_faction.captured_warriors.all()) == [undefended_rival.leader]
    assert Transaction.objects.current_balance(faction_id=undefended_rival.id) == 400
    assert Transaction.objects.current_balance(faction_id=current_savegame.player_faction_id) == 400


@pytest.mark.django_db
def test_faction_occupy_view_refuses_a_rival_that_is_still_standing(
    logged_in_client, current_savegame, undefended_rival
):
    WarriorFactory(faction=undefended_rival)

    response = logged_in_client.post(reverse("faction:faction-occupy-view", kwargs={"pk": undefended_rival.id}))

    assert response.status_code == 404
    undefended_rival.refresh_from_db()
    assert undefended_rival.is_defeated is False


@pytest.mark.django_db
def test_faction_occupy_view_hides_factions_of_other_savegames(logged_in_client, current_savegame):
    foreign_faction = FactionFactory(savegame=SavegameFactory())
    foreign_faction.leader = WarriorFactory(
        faction=foreign_faction, condition=Warrior.ConditionChoices.CONDITION_UNCONSCIOUS
    )
    foreign_faction.save()

    response = logged_in_client.post(reverse("faction:faction-occupy-view", kwargs={"pk": foreign_faction.id}))

    assert response.status_code == 404
    foreign_faction.refresh_from_db()
    assert foreign_faction.is_defeated is False


@pytest.mark.django_db
def test_faction_occupy_view_without_a_player_faction(logged_in_client, savegame_without_player_faction):
    rival = FactionFactory(savegame=savegame_without_player_faction)
    rival.leader = WarriorFactory(faction=rival, condition=Warrior.ConditionChoices.CONDITION_UNCONSCIOUS)
    rival.save()

    response = logged_in_client.post(reverse("faction:faction-occupy-view", kwargs={"pk": rival.id}))

    assert response.status_code == 404
