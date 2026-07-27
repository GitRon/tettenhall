import factory
from factory.django import DjangoModelFactory

from apps.faction.tests.factories.faction import FactionFactory
from apps.training.models import Training


class TrainingFactory(DjangoModelFactory):
    class Meta:
        model = Training

    category = Training.TrainingCategory.WEAPON_MASTERY
    faction = factory.SubFactory(FactionFactory)
