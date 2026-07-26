import factory
from factory.django import DjangoModelFactory

from apps.skirmish.models.battle_history import BattleHistory
from apps.skirmish.tests.factories.skirmish import SkirmishFactory


class BattleHistoryFactory(DjangoModelFactory):
    class Meta:
        model = BattleHistory

    message = factory.Sequence(lambda n: f"Battle log entry {n}")
    skirmish = factory.SubFactory(SkirmishFactory)
