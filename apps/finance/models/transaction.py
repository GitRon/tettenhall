from django.db import models

from apps.faction.models.faction import Faction
from apps.finance.managers.transaction import TransactionManager


class Transaction(models.Model):
    reason = models.CharField("Reason", max_length=100)
    amount = models.IntegerField("Amount")
    faction = models.ForeignKey(Faction, verbose_name="Faction", null=True, blank=True, on_delete=models.CASCADE)
    # TODO: add month

    objects = TransactionManager()

    class Meta:
        verbose_name = "Transaction"
        verbose_name_plural = "Transactions"
        default_related_name = "transaction"
        ordering = ("id",)

    def __str__(self) -> str:
        return f"{self.reason} ({self.amount} Silver)"
