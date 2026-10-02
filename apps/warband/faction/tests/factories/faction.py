import factory
from factory.django import DjangoModelFactory

from apps.warband.faction.models.faction import Faction
from apps.warband.faction.tests.factories.culture import CultureFactory
from apps.warband.savegame.tests.factories.savegame import SavegameFactory


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
    # Every faction owns exactly one town, created together with it in _create_faction, and
    # several handlers read faction.town. Referenced by path because the town factory points back here.
    # Pass town=None to skip it, or town__hall=... to set a building level.
    town = factory.RelatedFactory("apps.warband.town.tests.factories.town.TownFactory", factory_related_name="faction")

    @factory.post_generation
    def is_player(self, create, extracted, **kwargs):
        # FactionFactory(is_player=True) makes it the player's faction of its savegame. The savegame
        # cannot do this from its own side: its factory leaves player_faction empty, or the two recurse
        if create and extracted:
            self.savegame.player_faction = self
            self.savegame.save()
