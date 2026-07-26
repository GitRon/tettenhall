import factory
from factory.django import DjangoModelFactory

from apps.faction.tests.factories.faction import FactionFactory
from apps.skirmish.models.warrior import Warrior


class WarriorFactory(DjangoModelFactory):
    class Meta:
        model = Warrior

    name = factory.Sequence(lambda n: f"Warrior {n}")
    faction = factory.SubFactory(FactionFactory)
    # Keep warrior, faction and savegame consistent instead of creating a second savegame
    savegame = factory.SelfAttribute("faction.savegame")
    culture = factory.SelfAttribute("faction.culture")

    strength = 10
    dexterity = 10
    current_health = 20
    max_health = 20
    current_morale = 20
    max_morale = 20
