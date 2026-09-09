import pytest

from apps.warband.faction.tests.factories.faction import FactionFactory
from apps.warband.incident.incidents.base import IncidentOutcome
from apps.warband.incident.messages.events.incident import IncidentOccurred
from apps.warband.item.handlers.events.incident import handle_incident_lost_item
from apps.warband.item.messages.commands.item import LoseItem
from apps.warband.item.tests.factories.item import ItemFactory


@pytest.mark.django_db
def test_handle_incident_lost_item_hands_the_gear_over_to_be_destroyed():
    faction = FactionFactory()
    lost_item = ItemFactory(owner=faction, savegame=faction.savegame)
    outcome = IncidentOutcome(title="Wighelm has lost his spear.", body="", lost_item=lost_item)

    result = handle_incident_lost_item(context=IncidentOccurred(faction=faction, month=3, outcome=outcome))

    assert result == LoseItem(faction=faction, item=lost_item, month=3)


def test_handle_incident_lost_item_for_an_incident_that_takes_no_gear():
    faction = FactionFactory.build()

    result = handle_incident_lost_item(
        context=IncidentOccurred(faction=faction, month=3, outcome=IncidentOutcome(title="A relic.", body=""))
    )

    assert result is None
