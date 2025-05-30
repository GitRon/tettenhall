from django.db import models
from django.db.models import Sum, manager

from apps.faction.models.faction import Faction


class TransactionQuerySet(models.QuerySet):
    def for_savegame(self, *, savegame_id: int):
        return self.filter(faction__player_savegame=savegame_id)


class TransactionManager(manager.Manager):
    def create_transaction(self, *, reason: str, amount: int, faction: Faction, month: int):
        # TODO: call this only in a command, not directly
        return self.create(reason=reason, amount=amount, faction=faction, month=month)

    def current_balance(self, *, savegame_id: int) -> int:
        # TODO: this is not multi-tenant ready
        return self.for_savegame(savegame_id=savegame_id).aggregate(sum_amount=Sum("amount"))["sum_amount"] or 0


TransactionManager = TransactionManager.from_queryset(TransactionQuerySet)
