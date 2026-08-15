from django.db import models
from django.db.models import Sum, manager

from apps.faction.models.faction import Faction


class TransactionQuerySet(models.QuerySet):
    def for_faction(self, *, faction_id: int):
        # Every faction of a savegame keeps its own purse, the NPC rivals included, so a balance is
        # only ever a question about one faction. This used to be reached by joining
        # faction__player_savegame, which resolved to the player faction as well - via the reverse
        # side of Savegame.player_faction - but only for the player, and only by accident of that
        # relation being a OneToOne. Asking for the faction directly is the same query, minus the join
        return self.filter(faction_id=faction_id)

    def for_player_faction(self, *, faction_id: int):
        # The name PlayerFactionScopedQuerysetMixin looks for; a ledger is faction-scoped either way
        return self.for_faction(faction_id=faction_id)


class TransactionManager(manager.Manager):
    def create_transaction(self, *, reason: str, amount: int, faction: Faction, month: int):
        return self.create(reason=reason, amount=amount, faction=faction, month=month)

    def current_balance(self, *, faction_id: int) -> int:
        return self.for_faction(faction_id=faction_id).aggregate(sum_amount=Sum("amount"))["sum_amount"] or 0


TransactionManager = TransactionManager.from_queryset(TransactionQuerySet)
