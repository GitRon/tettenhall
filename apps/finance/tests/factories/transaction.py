import factory
from factory.django import DjangoModelFactory

from apps.faction.tests.factories.faction import FactionFactory
from apps.finance.models.transaction import Transaction


class TransactionFactory(DjangoModelFactory):
    class Meta:
        model = Transaction

    reason = factory.Sequence(lambda n: f"Transaction {n}")
    amount = 100
    faction = factory.SubFactory(FactionFactory)
    month = 1
