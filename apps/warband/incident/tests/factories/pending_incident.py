import factory
from factory.django import DjangoModelFactory

from apps.warband.faction.tests.factories.faction import FactionFactory
from apps.warband.incident.incidents.burnt_village_refugees import BurntVillageRefugees
from apps.warband.incident.models.pending_incident import PendingIncident


class PendingIncidentFactory(DjangoModelFactory):
    class Meta:
        model = PendingIncident

    faction = factory.SubFactory(FactionFactory)
    month = 1
    # A real entry of the pool, because answering looks the class up by this name
    incident = BurntVillageRefugees.__name__
    title = BurntVillageRefugees.TITLE
    body = BurntVillageRefugees.BODY
