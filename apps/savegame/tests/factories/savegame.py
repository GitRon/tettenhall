import factory
from factory.django import DjangoModelFactory

from apps.account.tests.factories.user import UserFactory
from apps.savegame.models.savegame import Savegame


class SavegameFactory(DjangoModelFactory):
    class Meta:
        model = Savegame

    name = factory.Sequence(lambda n: f"Savegame {n}")
    created_by = factory.SubFactory(UserFactory)
    is_active = True
    current_month = 1
    # Set via the faction factory, otherwise this would recurse
    player_faction = None
