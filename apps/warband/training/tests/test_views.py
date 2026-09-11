import pytest
from django.urls import reverse

from apps.warband.faction.tests.factories.faction import FactionFactory
from apps.warband.training.models.training import Training
from apps.warband.training.tests.factories.training import TrainingFactory


@pytest.mark.django_db
def test_training_edit_view_shows_the_training(logged_in_client, current_savegame):
    training = TrainingFactory(faction=current_savegame.player_faction)

    response = logged_in_client.get(reverse("warband:training-edit-view", kwargs={"pk": training.id}))

    assert response.status_code == 200
    assert response.context["training"] == training


@pytest.mark.django_db
def test_training_edit_view_changes_the_category(logged_in_client, current_savegame):
    training = TrainingFactory(faction=current_savegame.player_faction)

    response = logged_in_client.post(
        reverse("warband:training-edit-view", kwargs={"pk": training.id}),
        data={"category": Training.TrainingCategory.SHIELD_WALL},
    )

    assert response.status_code == 302
    training.refresh_from_db()
    assert training.category == Training.TrainingCategory.SHIELD_WALL


@pytest.mark.django_db
def test_training_edit_view_returns_to_the_month(logged_in_client, current_savegame):
    """
    The choice is read and made on the month's page, so that is where saving it goes back to.
    """
    training = TrainingFactory(faction=current_savegame.player_faction)

    response = logged_in_client.post(
        reverse("warband:training-edit-view", kwargs={"pk": training.id}),
        data={"category": Training.TrainingCategory.SHIELD_WALL},
    )

    assert response.url == reverse("warband:dashboard-view")


@pytest.mark.django_db
def test_training_edit_view_cannot_change_a_training_of_another_savegame(logged_in_client, current_savegame):
    foreign_training = TrainingFactory(category=Training.TrainingCategory.WEAPON_MASTERY)

    response = logged_in_client.post(
        reverse("warband:training-edit-view", kwargs={"pk": foreign_training.id}),
        data={"category": Training.TrainingCategory.SHIELD_WALL},
    )

    assert response.status_code == 404
    foreign_training.refresh_from_db()
    assert foreign_training.category == Training.TrainingCategory.WEAPON_MASTERY


@pytest.mark.django_db
def test_training_edit_view_cannot_change_the_training_of_a_rival_faction(logged_in_client, current_savegame):
    """
    Editing a rival's row changes what its warriors improve each month, so being in the same
    savegame must not be enough.
    """
    rival_faction = FactionFactory(savegame=current_savegame)
    rival_training = TrainingFactory(faction=rival_faction, category=Training.TrainingCategory.WEAPON_MASTERY)

    response = logged_in_client.post(
        reverse("warband:training-edit-view", kwargs={"pk": rival_training.id}),
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
        reverse("warband:training-edit-view", kwargs={"pk": training.id}),
        data={"category": Training.TrainingCategory.SHIELD_WALL},
    )

    assert response.status_code == 404
    training.refresh_from_db()
    assert training.category == Training.TrainingCategory.WEAPON_MASTERY
