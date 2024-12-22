from django.db import models
from django.db.models import manager

from apps.faction.models.faction import Faction


class TransactionQuerySet(models.QuerySet):
    pass


class TransactionManager(manager.Manager):
    def create_transaction(self, reason: str, amount: int, faction: Faction):
        return self.create(reason=reason, amount=amount, faction=faction)


TransactionManager = TransactionManager.from_queryset(TransactionQuerySet)
