import factory
from factory.django import DjangoModelFactory

from apps.faction.tests.factories.faction import FactionFactory
from apps.month.models.player_month_log import PlayerMonthLog


class PlayerMonthLogFactory(DjangoModelFactory):
    class Meta:
        model = PlayerMonthLog

    title = factory.Sequence(lambda n: f"Month log {n}")
    kind = PlayerMonthLog.KindChoices.KIND_SALARIES_PAID
    # Kept consistent with the kind above the way create_record() derives it, so a factory-built row
    # is not the one place in the project where the two disagree
    category = PlayerMonthLog.KIND_CATEGORIES[PlayerMonthLog.KindChoices.KIND_SALARIES_PAID]
    month = 1
    faction = factory.SubFactory(FactionFactory)
