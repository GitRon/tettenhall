import pytest
from django.urls import reverse

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
