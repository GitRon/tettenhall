import factory
from factory.django import DjangoModelFactory

from apps.warband.skirmish.models.skirmish_warrior_growth import SkirmishWarriorGrowth
from apps.warband.skirmish.tests.factories.skirmish import SkirmishFactory
from apps.warband.skirmish.tests.factories.warrior import WarriorFactory


class SkirmishWarriorGrowthFactory(DjangoModelFactory):
    class Meta:
        model = SkirmishWarriorGrowth

    skirmish = factory.SubFactory(SkirmishFactory)
    warrior = factory.SubFactory(WarriorFactory, faction=factory.SelfAttribute("..skirmish.attacking_faction"))
    faction = factory.SelfAttribute("warrior.faction")
    gained_experience = 10
