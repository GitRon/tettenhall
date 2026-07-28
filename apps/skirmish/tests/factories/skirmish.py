import factory
from factory.django import DjangoModelFactory

from apps.faction.tests.factories.faction import FactionFactory
from apps.skirmish.models.skirmish import Skirmish


class SkirmishFactory(DjangoModelFactory):
    class Meta:
        model = Skirmish

    name = factory.Sequence(lambda n: f"Skirmish {n}")
    player_faction = factory.SubFactory(FactionFactory)
    # Keep both factions inside the same savegame
    non_player_faction = factory.SubFactory(FactionFactory, savegame=factory.SelfAttribute("..player_faction.savegame"))
