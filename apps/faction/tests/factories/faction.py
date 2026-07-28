import factory
from factory.django import DjangoModelFactory

from apps.faction.models.faction import Faction
from apps.faction.tests.factories.culture import CultureFactory
from apps.savegame.tests.factories.savegame import SavegameFactory


class FactionFactory(DjangoModelFactory):
    class Meta:
        model = Faction
        # The town below does not touch the faction, so re-saving it afterwards is pointless
        skip_postgeneration_save = True

    name = factory.Sequence(lambda n: f"Faction {n}")
    town_name = factory.Sequence(lambda n: f"Town {n}")
    culture = factory.SubFactory(CultureFactory)
    savegame = factory.SubFactory(SavegameFactory)
    fyrd_reserve = 3
    # Every faction owns exactly one town, created together with it in handle_create_new_faction, and
    # several handlers read faction.town. Referenced by path because the town factory points back here.
    # Pass town=None to skip it, or town__hall=... to set a building level.
    town = factory.RelatedFactory("apps.town.tests.factories.town.TownFactory", factory_related_name="faction")
