import factory
from factory.django import DjangoModelFactory

from apps.faction.models.faction import Faction


class FactionFactory(DjangoModelFactory):
    class Meta:
        model = Faction

    name = factory.Sequence(lambda n: f"Test Faction {n}")
    town_name = factory.Sequence(lambda n: f"Test Town {n}")
    fyrd_reserve = 0

    @factory.post_generation
    def available_items(self, create, extracted, **kwargs):
        if not create:
            return

        if extracted:
            for item in extracted:
                self.available_items.add(item)
