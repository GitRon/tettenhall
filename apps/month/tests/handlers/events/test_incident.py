from apps.faction.tests.factories.faction import FactionFactory
from apps.incident.incidents.base import IncidentOutcome
from apps.incident.messages.events.incident import IncidentOccurred
from apps.month.handlers.events.incident import handle_write_incident_to_month_log
from apps.month.messages.commands.month import CreatePlayerMonthLog
from apps.month.models.player_month_log import PlayerMonthLog


def test_handle_write_incident_to_month_log_carries_both_sentences():
    faction = FactionFactory.build()
    outcome = IncidentOutcome(title="The hall roof came down in the night.", body="Nobody was beneath it.")

    result = handle_write_incident_to_month_log(context=IncidentOccurred(faction=faction, month=3, outcome=outcome))

    assert result == CreatePlayerMonthLog(
        title="The hall roof came down in the night.",
        body="Nobody was beneath it.",
        kind=PlayerMonthLog.KindChoices.KIND_INCIDENT,
        month=3,
        faction=faction,
    )
