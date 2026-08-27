import pytest
from django.contrib.messages import get_messages
from django.urls import reverse

from apps.faction.tests.factories.faction import FactionFactory
from apps.quest.models.quest_contract import QuestContract
from apps.quest.tests.factories.quest import QuestFactory
from apps.savegame.models.savegame import Savegame
from apps.savegame.tests.factories.savegame import SavegameFactory
from apps.skirmish.models.skirmish import Skirmish
from apps.skirmish.models.warrior import Warrior
from apps.skirmish.tests.factories.warrior import WarriorFactory


@pytest.mark.django_db
def test_quest_accept_view_signs_a_contract_and_sets_up_the_skirmish(logged_in_client, current_savegame):
    """
    Flow test: no mocking inside the chain, so this runs the real queue and asserts the end state.
    """
    quest = QuestFactory(target_faction__savegame=current_savegame)
    WarriorFactory(faction=quest.target_faction)
    warrior = WarriorFactory(faction=current_savegame.player_faction)
    current_savegame.player_faction.available_quests.add(quest)

    response = logged_in_client.post(
        reverse("quest:quest-accept-view", kwargs={"pk": quest.pk}),
        data={
            "faction": current_savegame.player_faction.id,
            "quest": quest.id,
            "assigned_warriors": [warrior.id],
        },
    )

    assert response.status_code == 302
    assert [str(message) for message in get_messages(response.wsgi_request)] == [f'You accepted the quest "{quest}".']
    quest_contract = QuestContract.objects.get(quest=quest, faction=current_savegame.player_faction)
    assert list(quest_contract.assigned_warriors.all()) == [warrior]
    assert quest_contract.skirmish is not None


@pytest.mark.django_db
def test_quest_accept_view_sends_the_player_home_on_a_finished_savegame(logged_in_client, current_savegame):
    """
    The full-page branch of RunningSavegameRequiredMixin. This is a plain navigation, not an htmx
    fragment, and a browser handed a 204 abandons the navigation: the page does not change and the
    player is told nothing. A redirect carrying a warning is the same refusal he can actually see.
    """
    quest = QuestFactory(target_faction__savegame=current_savegame)
    WarriorFactory(faction=quest.target_faction)
    current_savegame.player_faction.available_quests.add(quest)
    current_savegame.outcome = Savegame.OutcomeChoices.OUTCOME_LOST
    current_savegame.save()

    response = logged_in_client.get(reverse("quest:quest-accept-view", kwargs={"pk": quest.pk}))

    assert response.status_code == 302
    assert response.url == reverse("account:dashboard-view")
    assert [str(message) for message in get_messages(response.wsgi_request)] == [
        "This game is over. Start a new savegame to play on."
    ]


@pytest.mark.django_db
def test_quest_accept_view_redisplays_the_quest_on_an_invalid_submission(logged_in_client, current_savegame):
    quest = QuestFactory(target_faction__savegame=current_savegame)
    WarriorFactory(faction=quest.target_faction)
    current_savegame.player_faction.available_quests.add(quest)

    response = logged_in_client.post(reverse("quest:quest-accept-view", kwargs={"pk": quest.pk}), data={})

    assert response.status_code == 200
    assert response.context["object"] == quest
    assert QuestContract.objects.exists() is False


@pytest.mark.django_db
def test_quest_accept_view_cannot_accept_a_quest_that_was_never_offered(logged_in_client, current_savegame):
    """
    Belonging to the right savegame is not enough - a quest is only acceptable once it is pinned to
    the player's own bulletin board.
    """
    unoffered_quest = QuestFactory(target_faction__savegame=current_savegame)
    WarriorFactory(faction=unoffered_quest.target_faction)
    warrior = WarriorFactory(faction=current_savegame.player_faction)

    response = logged_in_client.post(
        reverse("quest:quest-accept-view", kwargs={"pk": unoffered_quest.pk}),
        data={
            "faction": current_savegame.player_faction.id,
            "quest": unoffered_quest.id,
            "assigned_warriors": [warrior.id],
        },
    )

    assert response.status_code == 404
    assert QuestContract.objects.exists() is False


@pytest.mark.django_db
def test_quest_accept_view_refuses_a_quest_whose_target_fields_nobody(logged_in_client, current_savegame):
    """
    The card goes stale inside the month it was offered in - the player beats the target after it was
    pinned. The opposition is that faction's own war band, and staging a fight against an empty side
    raises one hop into the queue, so the view refuses before anything is signed.
    """
    quest = QuestFactory(target_faction__savegame=current_savegame)
    WarriorFactory(faction=quest.target_faction, condition=Warrior.ConditionChoices.CONDITION_UNCONSCIOUS)
    current_savegame.player_faction.available_quests.add(quest)
    warrior = WarriorFactory(faction=current_savegame.player_faction)

    response = logged_in_client.post(
        reverse("quest:quest-accept-view", kwargs={"pk": quest.pk}),
        data={
            "faction": current_savegame.player_faction.id,
            "quest": quest.id,
            "assigned_warriors": [warrior.id],
        },
    )

    assert response.status_code == 404
    assert QuestContract.objects.exists() is False


@pytest.mark.django_db
def test_quest_accept_view_rejects_a_hidden_quest_field_naming_another_quest(logged_in_client, current_savegame):
    """
    "quest" is a hidden input, so its queryset has to do the validating: left at the default the
    posted id would decide which quest gets accepted, not the scoped one from the URL.
    """
    quest = QuestFactory(target_faction__savegame=current_savegame)
    WarriorFactory(faction=quest.target_faction)
    current_savegame.player_faction.available_quests.add(quest)
    other_quest = QuestFactory(target_faction__savegame=current_savegame)
    WarriorFactory(faction=other_quest.target_faction)
    current_savegame.player_faction.available_quests.add(other_quest)
    warrior = WarriorFactory(faction=current_savegame.player_faction)

    response = logged_in_client.post(
        reverse("quest:quest-accept-view", kwargs={"pk": quest.pk}),
        data={
            "faction": current_savegame.player_faction.id,
            "quest": other_quest.id,
            "assigned_warriors": [warrior.id],
        },
    )

    assert response.status_code == 200
    assert QuestContract.objects.exists() is False


@pytest.mark.django_db
def test_quest_accept_view_rejects_a_hidden_faction_field_naming_another_faction(logged_in_client, current_savegame):
    """
    Same for "faction": the posted id must not be able to sign the contract for somebody else.
    """
    quest = QuestFactory(target_faction__savegame=current_savegame)
    WarriorFactory(faction=quest.target_faction)
    current_savegame.player_faction.available_quests.add(quest)
    rival_faction = FactionFactory(savegame=current_savegame)
    warrior = WarriorFactory(faction=current_savegame.player_faction)

    response = logged_in_client.post(
        reverse("quest:quest-accept-view", kwargs={"pk": quest.pk}),
        data={
            "faction": rival_faction.id,
            "quest": quest.id,
            "assigned_warriors": [warrior.id],
        },
    )

    assert response.status_code == 200
    assert QuestContract.objects.exists() is False


@pytest.mark.django_db
def test_quest_accept_view_without_a_player_faction(logged_in_client, savegame_without_player_faction):
    """
    No faction means no bulletin board to accept from, so the scoping narrows to nothing instead of
    dereferencing a missing faction.
    """
    quest = QuestFactory(target_faction__savegame=savegame_without_player_faction)

    response = logged_in_client.post(reverse("quest:quest-accept-view", kwargs={"pk": quest.pk}), data={})

    assert response.status_code == 404
    assert QuestContract.objects.exists() is False


@pytest.mark.django_db
def test_quest_accept_view_cannot_accept_a_quest_of_another_savegame(logged_in_client, current_savegame):
    """
    Without the savegame scoping the id from the URL would be enough to accept another player's quest.
    """
    other_savegame = SavegameFactory()
    foreign_quest = QuestFactory(target_faction__savegame=other_savegame)
    warrior = WarriorFactory(faction=current_savegame.player_faction)

    response = logged_in_client.post(
        reverse("quest:quest-accept-view", kwargs={"pk": foreign_quest.pk}),
        data={
            "faction": current_savegame.player_faction.id,
            "quest": foreign_quest.id,
            "assigned_warriors": [warrior.id],
        },
    )

    assert response.status_code == 404
    assert QuestContract.objects.filter(quest=foreign_quest).exists() is False


@pytest.mark.django_db
def test_quest_accept_view_takes_the_targets_defenders_out_of_reach_of_a_march(
    logged_in_client, current_savegame, queuebie_registry
):
    """
    Flow test, because what it pins is a savegame that could not be finished, and only a real queue run
    creates the two skirmishes.

    Accepting a quest commits the target's war band. Marching on the same rival afterwards used to
    muster the very same men onto a second skirmish; whichever was resolved first killed them, leaving
    the other with nobody healthy to post. The fight view then refuses the round and the month refuses
    to turn while a skirmish is open - the game simply stops. Now the rival is no longer a legitimate
    target while its defenders are spoken for.
    """
    player_faction = current_savegame.player_faction
    leader = WarriorFactory(faction=player_faction, savegame=current_savegame)
    player_faction.leader = leader
    player_faction.save()
    footman = WarriorFactory(faction=player_faction, savegame=current_savegame)
    rival_faction = FactionFactory(savegame=current_savegame)
    WarriorFactory(faction=rival_faction, savegame=current_savegame)
    quest = QuestFactory(target_faction=rival_faction)
    player_faction.available_quests.add(quest)
    logged_in_client.post(
        reverse("quest:quest-accept-view", kwargs={"pk": quest.pk}),
        data={"faction": player_faction.id, "quest": quest.id, "assigned_warriors": [footman.id]},
    )

    # The leader is added by the form, so an empty band still marches
    response = logged_in_client.post(
        reverse("faction:faction-attack-view", kwargs={"pk": rival_faction.pk}), data={"assigned_warriors": []}
    )

    assert response.status_code == 404
    assert Skirmish.objects.count() == 1


@pytest.mark.django_db
def test_quest_accept_view_without_an_active_savegame(logged_in_client):
    """
    Answering 404 rather than a server error: with no savegame there is no month to ask whether the
    target can still field a defender, and the scoped queryset narrows to nothing anyway.
    """
    quest = QuestFactory()
    WarriorFactory(faction=quest.target_faction)

    response = logged_in_client.get(reverse("quest:quest-accept-view", kwargs={"pk": quest.pk}))

    assert response.status_code == 404
    assert QuestContract.objects.exists() is False
