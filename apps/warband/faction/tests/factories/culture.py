import factory
from factory.django import DjangoModelFactory

from apps.warband.faction.models.culture import Culture


class CultureFactory(DjangoModelFactory):
    class Meta:
        model = Culture

    name = factory.Sequence(lambda n: f"Culture {n}")
    locale = "en_GB"
