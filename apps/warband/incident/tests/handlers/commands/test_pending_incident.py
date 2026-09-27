import pytest

from apps.warband.faction.tests.factories.faction import FactionFactory
from apps.warband.incident.handlers.commands.pending_incident import (
    handle_answer_open_pending_incidents,
    handle_answer_pending_incident,
)
from apps.warband.incident.incidents.base import IncidentOutcome
from apps.warband.incident.incidents.burnt_village_refugees import BurntVillageRefugees
from apps.warband.incident.messages.commands.pending_incident import AnswerOpenPendingIncidents, AnswerPendingIncident
from apps.warband.incident.messages.events.incident import IncidentOccurred
from apps.warband.incident.models.pending_incident import PendingIncident
from apps.warband.incident.tests.factories.pending_incident import PendingIncidentFactory


@pytest.mark.django_db
def test_handle_answer_pending_incident_lands_the_answer_and_closes_the_question():
    pending_incident = PendingIncidentFactory(month=4)
    option = BurntVillageRefugees.get_option(key="take_in")

    result = handle_answer_pending_incident(
        context=AnswerPendingIncident(pending_incident=pending_incident, option=option, month=4)
    )

    assert result == IncidentOccurred(
        faction=pending_incident.faction,
        month=4,
        outcome=IncidentOutcome(
            title=option.title,
            body=option.body,
            silver_change=option.silver_change,
            fyrd_change=option.fyrd_change,
        ),
    )
    assert PendingIncident.objects.exists() is False


@pytest.mark.django_db
def test_handle_answer_pending_incident_answers_nothing_the_second_time():
    """
    Two overlapping posts both find the question open - a double click, or two options clicked in
    quick succession. Only the first answer lands.
    """
    pending_incident = PendingIncidentFactory(month=4)
    handle_answer_pending_incident(
        context=AnswerPendingIncident(
            pending_incident=pending_incident, option=BurntVillageRefugees.get_option(key="take_in"), month=4
        )
    )

    result = handle_answer_pending_incident(
        context=AnswerPendingIncident(
            pending_incident=pending_incident, option=BurntVillageRefugees.get_default_option(), month=4
        )
    )

    assert result is None


@pytest.mark.django_db
def test_handle_answer_open_pending_incidents_lands_the_default_in_the_new_month():
    """
    Dated to the month now beginning, so the line survives the log clearing and the player reads what
    his silence decided.
    """
    pending_incident = PendingIncidentFactory(month=4)
    default_option = BurntVillageRefugees.get_default_option()

    result = handle_answer_open_pending_incidents(
        context=AnswerOpenPendingIncidents(faction=pending_incident.faction, month=5)
    )

    assert result == [
        IncidentOccurred(
            faction=pending_incident.faction,
            month=5,
            outcome=IncidentOutcome(title=default_option.title, body=default_option.body),
        )
    ]
    assert PendingIncident.objects.exists() is False


@pytest.mark.django_db
def test_handle_answer_open_pending_incidents_leaves_this_months_question_alone():
    """
    The month now beginning may just have asked something, and that question is the player's to
    answer.
    """
    pending_incident = PendingIncidentFactory(month=5)

    result = handle_answer_open_pending_incidents(
        context=AnswerOpenPendingIncidents(faction=pending_incident.faction, month=5)
    )

    assert result == []
    assert PendingIncident.objects.exists() is True


@pytest.mark.django_db
def test_handle_answer_open_pending_incidents_leaves_another_factions_question_alone():
    pending_incident = PendingIncidentFactory(month=4)

    result = handle_answer_open_pending_incidents(
        context=AnswerOpenPendingIncidents(faction=FactionFactory(savegame=pending_incident.faction.savegame), month=5)
    )

    assert result == []
    assert PendingIncident.objects.exists() is True
