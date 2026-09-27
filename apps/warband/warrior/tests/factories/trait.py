import factory
from factory.django import DjangoModelFactory

from apps.warband.skirmish.tests.factories.warrior import WarriorFactory
from apps.warband.warrior.models.trait import Trait
from apps.warband.warrior.tests.factories.trait_type import TraitTypeFactory


class TraitFactory(DjangoModelFactory):
    class Meta:
        model = Trait

    warrior = factory.SubFactory(WarriorFactory)
    type = factory.SubFactory(TraitTypeFactory)
