import pytest
from django.urls import reverse

from apps.faction.tests.factories.faction import FactionFactory
from apps.skirmish.models.warrior import Warrior
from apps.skirmish.tests.factories.warrior import WarriorFactory
from apps.training.models.training import Training
from apps.training.tests.factories.training import TrainingFactory


@pytest.mark.django_db
def test_training_list_view_provides_the_current_training(logged_in_client, current_savegame):
    training = TrainingFactory(faction=current_savegame.player_faction)

    response = logged_in_client.get(reverse("training:training-list-view"))

    assert response.status_code == 200
    assert response.context["current_training"] == training


@pytest.mark.django_db
def test_training_list_view_hides_trainings_of_another_savegame(logged_in_client, current_savegame):
    training = TrainingFactory(faction=current_savegame.player_faction)
    TrainingFactory()

    response = logged_in_client.get(reverse("training:training-list-view"))

    assert response.status_code == 200
    assert list(response.context["training_list"]) == [training]


@pytest.mark.django_db
def test_training_list_view_lists_the_living_roster(logged_in_client, current_savegame):
    """
    The month trains the healthy only, and the page used to walk every warrior of the faction - so a
    fleeing man sat there with progress bars and then did not move when the month turned. The dead
    are left off entirely, the way the faction page leaves them off its roster.
    """
    TrainingFactory(faction=current_savegame.player_faction)
    healthy_warrior = WarriorFactory(faction=current_savegame.player_faction, name="Aelfric")
    fleeing_warrior = WarriorFactory(
        faction=current_savegame.player_faction, name="Beorn", condition=Warrior.ConditionChoices.CONDITION_FLEEING
    )
    WarriorFactory(
        faction=current_savegame.player_faction, name="Cenwulf", condition=Warrior.ConditionChoices.CONDITION_DEAD
    )

    response = logged_in_client.get(reverse("training:training-list-view"))

    assert response.status_code == 200
    assert list(response.context["warrior_list"]) == [healthy_warrior, fleeing_warrior]


@pytest.mark.django_db
def test_training_list_view_lists_only_the_roster_of_the_player_faction(logged_in_client, current_savegame):
    """
    Every faction of the savegame has warriors, and only the player's own are in his training.
    """
    TrainingFactory(faction=current_savegame.player_faction)
    own_warrior = WarriorFactory(faction=current_savegame.player_faction)
    rival_faction = FactionFactory(savegame=current_savegame)
    WarriorFactory(faction=rival_faction)

    response = logged_in_client.get(reverse("training:training-list-view"))

    assert response.status_code == 200
    assert list(response.context["warrior_list"]) == [own_warrior]


@pytest.mark.django_db
def test_training_edit_view_shows_the_training(logged_in_client, current_savegame):
    training = TrainingFactory(faction=current_savegame.player_faction)

    response = logged_in_client.get(reverse("training:training-edit-view", kwargs={"pk": training.id}))

    assert response.status_code == 200
    assert response.context["training"] == training


@pytest.mark.django_db
def test_training_edit_view_changes_the_category(logged_in_client, current_savegame):
    training = TrainingFactory(faction=current_savegame.player_faction)

    response = logged_in_client.post(
        reverse("training:training-edit-view", kwargs={"pk": training.id}),
        data={"category": Training.TrainingCategory.SHIELD_WALL},
    )

    assert response.status_code == 302
    training.refresh_from_db()
    assert training.category == Training.TrainingCategory.SHIELD_WALL


@pytest.mark.django_db
def test_training_edit_view_cannot_change_a_training_of_another_savegame(logged_in_client, current_savegame):
    foreign_training = TrainingFactory(category=Training.TrainingCategory.WEAPON_MASTERY)

    response = logged_in_client.post(
        reverse("training:training-edit-view", kwargs={"pk": foreign_training.id}),
        data={"category": Training.TrainingCategory.SHIELD_WALL},
    )

    assert response.status_code == 404
    foreign_training.refresh_from_db()
    assert foreign_training.category == Training.TrainingCategory.WEAPON_MASTERY


@pytest.mark.django_db
def test_training_list_view_without_an_active_savegame(logged_in_client):
    """
    Neither the faction nor a training exists then, and the template reversed the edit url with an
    empty id.
    """
    response = logged_in_client.get(reverse("training:training-list-view"))

    assert response.status_code == 200
    assert response.context["current_training"] is None
    assert list(response.context["warrior_list"]) == []


@pytest.mark.django_db
def test_training_list_view_without_a_player_faction(logged_in_client, savegame_without_player_faction):
    """
    Both the training lookup and the roster need a faction id, so there is nothing to name yet.
    """
    response = logged_in_client.get(reverse("training:training-list-view"))

    assert response.status_code == 200
    assert response.context["current_training"] is None
    assert list(response.context["warrior_list"]) == []


@pytest.mark.django_db
def test_training_list_view_takes_the_training_of_the_player_faction(logged_in_client, current_savegame):
    """
    Every faction of the savegame owns a training row, so scoping to the savegame would show
    whichever one happens to come first - a rival's, half the time.
    """
    rival_faction = FactionFactory(savegame=current_savegame)
    TrainingFactory(faction=rival_faction)
    own_training = TrainingFactory(faction=current_savegame.player_faction)

    response = logged_in_client.get(reverse("training:training-list-view"))

    assert response.status_code == 200
    assert response.context["current_training"] == own_training


@pytest.mark.django_db
def test_training_edit_view_cannot_change_the_training_of_a_rival_faction(logged_in_client, current_savegame):
    """
    Editing a rival's row changes what its warriors improve each month, so being in the same
    savegame must not be enough.
    """
    rival_faction = FactionFactory(savegame=current_savegame)
    rival_training = TrainingFactory(faction=rival_faction, category=Training.TrainingCategory.WEAPON_MASTERY)

    response = logged_in_client.post(
        reverse("training:training-edit-view", kwargs={"pk": rival_training.id}),
        data={"category": Training.TrainingCategory.SHIELD_WALL},
    )

    assert response.status_code == 404
    rival_training.refresh_from_db()
    assert rival_training.category == Training.TrainingCategory.WEAPON_MASTERY


@pytest.mark.django_db
def test_training_edit_view_without_a_player_faction(logged_in_client, savegame_without_player_faction):
    """
    Nothing belongs to the player yet, so the player-faction scoping narrows to nothing.
    """
    training = TrainingFactory(category=Training.TrainingCategory.WEAPON_MASTERY)

    response = logged_in_client.post(
        reverse("training:training-edit-view", kwargs={"pk": training.id}),
        data={"category": Training.TrainingCategory.SHIELD_WALL},
    )

    assert response.status_code == 404
    training.refresh_from_db()
    assert training.category == Training.TrainingCategory.WEAPON_MASTERY
