import factory
from factory.django import DjangoModelFactory

from apps.warband.skirmish.tests.factories.warrior import WarriorFactory
from apps.warband.warrior.models.injury import Injury
from apps.warband.warrior.tests.factories.injury_type import InjuryTypeFactory


class InjuryFactory(DjangoModelFactory):
    class Meta:
        model = Injury

    warrior = factory.SubFactory(WarriorFactory)
    type = factory.SubFactory(InjuryTypeFactory)
    inflicted_in_month = 1
