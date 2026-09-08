import factory
from factory.django import DjangoModelFactory

from apps.skirmish.models.skirmish_casualty import SkirmishCasualty
from apps.skirmish.tests.factories.skirmish import SkirmishFactory
from apps.skirmish.tests.factories.warrior import WarriorFactory


class SkirmishCasualtyFactory(DjangoModelFactory):
    class Meta:
        model = SkirmishCasualty

    skirmish = factory.SubFactory(SkirmishFactory)
    warrior = factory.SubFactory(WarriorFactory, faction=factory.SelfAttribute("..skirmish.attacking_faction"))
    fate = SkirmishCasualty.FateChoices.FATE_KILLED
