import factory
from factory.django import DjangoModelFactory

from apps.faction.tests.factories.faction import FactionFactory
from apps.month.models.player_month_log import PlayerMonthLog


class PlayerMonthLogFactory(DjangoModelFactory):
    class Meta:
        model = PlayerMonthLog

    title = factory.Sequence(lambda n: f"Month log {n}")
    month = 1
    faction = factory.SubFactory(FactionFactory)
