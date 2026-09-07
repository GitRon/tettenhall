import pytest

from apps.incident.incidents.base import IncidentOutcome
from apps.incident.messages.events.incident import IncidentOccurred
from apps.skirmish.tests.factories.warrior import WarriorFactory
from apps.warrior.handlers.events.incident import handle_incident_max_morale
from apps.warrior.messages.commands.warrior import ChangeWarriorMaxMorale


@pytest.mark.django_db
def test_handle_incident_max_morale_names_the_man_and_the_share():
    warrior = WarriorFactory()
    outcome = IncidentOutcome(title="A relic came.", body="", max_morale_share=0.2, warrior=warrior)

    result = handle_incident_max_morale(context=IncidentOccurred(faction=warrior.faction, month=3, outcome=outcome))

    assert result == ChangeWarriorMaxMorale(warrior=warrior, faction=warrior.faction, share=0.2, month=3)


@pytest.mark.django_db
def test_handle_incident_max_morale_for_an_incident_that_only_names_a_man():
    """
    Keyed on the share, not on the warrior: an entry may put a man in its title without touching
    his nerve.
    """
    warrior = WarriorFactory()
    outcome = IncidentOutcome(title="Wighelm has lost his spear.", body="", warrior=warrior)

    result = handle_incident_max_morale(context=IncidentOccurred(faction=warrior.faction, month=3, outcome=outcome))

    assert result is None
