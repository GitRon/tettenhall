import factory
from factory.django import DjangoModelFactory

from apps.warband.faction.tests.factories.faction import FactionFactory
from apps.warband.town.models import Town


class TownFactory(DjangoModelFactory):
    class Meta:
        model = Town

    # The faction factory builds a town of its own, which the one-to-one would collide with
    faction = factory.SubFactory(FactionFactory, town=None)
