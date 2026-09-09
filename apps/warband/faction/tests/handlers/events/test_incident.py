from apps.warband.faction.handlers.events.incident import handle_incident_fyrd_reserve
from apps.warband.faction.messages.commands.faction import ChangeFyrdReserve
from apps.warband.faction.tests.factories.faction import FactionFactory
from apps.warband.incident.incidents.base import IncidentOutcome
from apps.warband.incident.messages.events.incident import IncidentOccurred


def test_handle_incident_fyrd_reserve_passes_the_change_on():
    faction = FactionFactory.build()
    outcome = IncidentOutcome(title="Villagers came in.", body="", fyrd_change=2)

    result = handle_incident_fyrd_reserve(context=IncidentOccurred(faction=faction, month=3, outcome=outcome))

    assert result == ChangeFyrdReserve(faction=faction, change=2, month=3)


def test_handle_incident_fyrd_reserve_for_an_incident_that_leaves_it_alone():
    faction = FactionFactory.build()

    result = handle_incident_fyrd_reserve(
        context=IncidentOccurred(faction=faction, month=3, outcome=IncidentOutcome(title="A relic.", body=""))
    )

    assert result is None
