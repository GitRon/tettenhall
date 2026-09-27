import pytest

from apps.warband.faction.tests.factories.faction import FactionFactory
from apps.warband.incident.models.pending_incident import PendingIncident
from apps.warband.incident.tests.factories.pending_incident import PendingIncidentFactory


@pytest.mark.django_db
def test_for_savegame_excludes_another_savegame():
    pending_incident = PendingIncidentFactory()
    PendingIncidentFactory()

    result = PendingIncident.objects.for_savegame(savegame_id=pending_incident.faction.savegame_id)

    assert list(result) == [pending_incident]


@pytest.mark.django_db
def test_for_player_faction_excludes_a_rival_in_the_same_savegame():
    pending_incident = PendingIncidentFactory()
    PendingIncidentFactory(faction=FactionFactory(savegame=pending_incident.faction.savegame))

    result = PendingIncident.objects.for_player_faction(faction_id=pending_incident.faction_id)

    assert list(result) == [pending_incident]


@pytest.mark.django_db
def test_asked_before_excludes_the_month_itself():
    earlier_incident = PendingIncidentFactory(month=4)
    PendingIncidentFactory(month=5)

    result = PendingIncident.objects.asked_before(month=5)

    assert list(result) == [earlier_incident]
