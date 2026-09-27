from apps.warband.incident.tests.factories.pending_incident import PendingIncidentFactory


def test_str_is_the_question_asked():
    pending_incident = PendingIncidentFactory.build(title="The abbot asked for lead.")

    assert str(pending_incident) == "The abbot asked for lead."
