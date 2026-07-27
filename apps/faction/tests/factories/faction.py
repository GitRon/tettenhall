import factory
from factory.django import DjangoModelFactory

from apps.faction.models.faction import Faction
from apps.faction.tests.factories.culture import CultureFactory
from apps.savegame.tests.factories.savegame import SavegameFactory


class FactionFactory(DjangoModelFactory):
    class Meta:
        model = Faction

    name = factory.Sequence(lambda n: f"Faction {n}")
    town_name = factory.Sequence(lambda n: f"Town {n}")
    culture = factory.SubFactory(CultureFactory)
    savegame = factory.SubFactory(SavegameFactory)
    fyrd_reserve = 3
