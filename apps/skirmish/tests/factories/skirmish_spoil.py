import factory
from factory.django import DjangoModelFactory

from apps.skirmish.models.skirmish_spoil import SkirmishSpoil
from apps.skirmish.tests.factories.skirmish import SkirmishFactory


class SkirmishSpoilFactory(DjangoModelFactory):
    class Meta:
        model = SkirmishSpoil

    skirmish = factory.SubFactory(SkirmishFactory)
    # The attacker by default, so a spoil belongs to a side of its own fight without a second savegame
    faction = factory.SelfAttribute("skirmish.attacking_faction")
    kind = SkirmishSpoil.KindChoices.KIND_SILVER_LOOTED
    amount = 10
