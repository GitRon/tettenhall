from apps.warband.faction.tests.factories.faction import FactionFactory
from apps.warband.finance.handlers.events.incident import handle_incident_silver
from apps.warband.finance.messages.commands.transaction import CreateTransaction
from apps.warband.incident.incidents.base import IncidentOutcome
from apps.warband.incident.messages.events.incident import IncidentOccurred


def test_handle_incident_silver_books_what_it_cost():
    faction = FactionFactory.build()
    outcome = IncidentOutcome(title="The hall roof came down in the night.", body="", silver_change=-180)

    result = handle_incident_silver(context=IncidentOccurred(faction=faction, month=3, outcome=outcome))

    assert result == CreateTransaction(
        reason="The hall roof came down in the night.",
        amount=-180,
        faction=faction,
        month=3,
    )


def test_handle_incident_silver_for_an_incident_that_costs_nothing():
    faction = FactionFactory.build()

    result = handle_incident_silver(
        context=IncidentOccurred(faction=faction, month=3, outcome=IncidentOutcome(title="A relic.", body=""))
    )

    assert result is None
