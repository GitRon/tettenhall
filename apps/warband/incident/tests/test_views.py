import pytest
from django.urls import reverse

from apps.warband.faction.tests.factories.faction import FactionFactory
from apps.warband.finance.models import Transaction
from apps.warband.finance.tests.factories.transaction import TransactionFactory
from apps.warband.incident.models.pending_incident import PendingIncident
from apps.warband.incident.tests.factories.pending_incident import PendingIncidentFactory
from apps.warband.savegame.tests.factories.savegame import SavegameFactory


@pytest.mark.django_db
def test_pending_incident_answer_view_lands_the_answer(logged_in_client, current_savegame):
    """
    The whole chain behind one answer: the question closes and the levers of the option given apply.
    """
    TransactionFactory(faction=current_savegame.player_faction, amount=500)
    pending_incident = PendingIncidentFactory(faction=current_savegame.player_faction)

    logged_in_client.post(
        reverse("warband:pending-incident-answer-view", kwargs={"pk": pending_incident.pk}),
        data={"option": "take_in"},
    )

    assert PendingIncident.objects.exists() is False
    assert Transaction.objects.filter(faction=current_savegame.player_faction, amount=-120).exists() is True


@pytest.mark.django_db
def test_pending_incident_answer_view_sends_the_player_back_to_the_month(logged_in_client, current_savegame):
    TransactionFactory(faction=current_savegame.player_faction, amount=500)
    pending_incident = PendingIncidentFactory(faction=current_savegame.player_faction)

    response = logged_in_client.post(
        reverse("warband:pending-incident-answer-view", kwargs={"pk": pending_incident.pk}),
        data={"option": "take_in"},
    )

    assert response.status_code == 200
    assert "HX-Redirect" in response.headers


@pytest.mark.django_db
def test_pending_incident_answer_view_rejects_an_option_the_entry_does_not_declare(logged_in_client, current_savegame):
    """
    A key naming nothing is a request no page offered, turned away before anything is dispatched.
    """
    pending_incident = PendingIncidentFactory(faction=current_savegame.player_faction)

    response = logged_in_client.post(
        reverse("warband:pending-incident-answer-view", kwargs={"pk": pending_incident.pk}),
        data={"option": "burn_them"},
    )

    assert response.status_code == 400
    assert PendingIncident.objects.exists() is True


@pytest.mark.django_db
def test_pending_incident_answer_view_refuses_an_answer_no_longer_affordable(logged_in_client, current_savegame):
    pending_incident = PendingIncidentFactory(faction=current_savegame.player_faction)

    response = logged_in_client.post(
        reverse("warband:pending-incident-answer-view", kwargs={"pk": pending_incident.pk}),
        data={"option": "take_in"},
    )

    assert response.status_code == 204
    assert "HX-Trigger" in response.headers


@pytest.mark.django_db
def test_pending_incident_answer_view_cannot_answer_a_rivals_question(logged_in_client, current_savegame):
    """
    Scoped to the player faction, not the savegame: the id from the URL must not reach a question put
    to anybody else in it.
    """
    pending_incident = PendingIncidentFactory(faction=FactionFactory(savegame=current_savegame))

    response = logged_in_client.post(
        reverse("warband:pending-incident-answer-view", kwargs={"pk": pending_incident.pk}),
        data={"option": "turn_away"},
    )

    assert response.status_code == 404


@pytest.mark.django_db
def test_pending_incident_answer_view_cannot_answer_another_savegames_question(logged_in_client, current_savegame):
    pending_incident = PendingIncidentFactory(faction=FactionFactory(savegame=SavegameFactory()))

    response = logged_in_client.post(
        reverse("warband:pending-incident-answer-view", kwargs={"pk": pending_incident.pk}),
        data={"option": "turn_away"},
    )

    assert response.status_code == 404
