from django.db import models
from django.db.models import Sum, manager

from apps.faction.models.faction import Faction


class TransactionQuerySet(models.QuerySet):
    def for_faction(self, *, faction_id: int):
        # Every faction of a savegame keeps its own purse, the NPC rivals included, so a balance is
        # only ever a question about one faction - scoping by savegame would add up all of them
        return self.filter(faction_id=faction_id)

    def for_player_faction(self, *, faction_id: int):
        # The name PlayerFactionScopedQuerysetMixin looks for; a ledger is faction-scoped either way
        return self.for_faction(faction_id=faction_id)


class TransactionManager(manager.Manager):
    def create_transaction(self, *, reason: str, amount: int, faction: Faction, month: int):
        # TODO: call this only in a command, not directly
        return self.create(reason=reason, amount=amount, faction=faction, month=month)

    def current_balance(self, *, faction_id: int) -> int:
        return self.for_faction(faction_id=faction_id).aggregate(sum_amount=Sum("amount"))["sum_amount"] or 0


TransactionManager = TransactionManager.from_queryset(TransactionQuerySet)
