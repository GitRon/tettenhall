import factory
from factory.django import DjangoModelFactory

from apps.faction.tests.factories.faction import FactionFactory
from apps.skirmish.models.skirmish import Skirmish


class SkirmishFactory(DjangoModelFactory):
    class Meta:
        model = Skirmish

    name = factory.Sequence(lambda n: f"Skirmish {n}")
    attacking_faction = factory.SubFactory(FactionFactory)
    # Keep both factions inside the same savegame
    defending_faction = factory.SubFactory(
        FactionFactory, savegame=factory.SelfAttribute("..attacking_faction.savegame")
    )
