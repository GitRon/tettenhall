import factory
from factory.django import DjangoModelFactory

from apps.warband.faction.tests.factories.faction import FactionFactory
from apps.warband.finance.models.transaction import Transaction


class TransactionFactory(DjangoModelFactory):
    class Meta:
        model = Transaction

    reason = factory.Sequence(lambda n: f"Transaction {n}")
    amount = 100
    faction = factory.SubFactory(FactionFactory)
    month = 1
