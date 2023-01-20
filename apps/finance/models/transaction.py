from django.db import models

from apps.faction.models.faction import Faction


class Transaction(models.Model):
    reason = models.CharField("Reason", max_length=100)
    amount = models.DecimalField("Amount", max_digits=8, decimal_places=0)
    faction = models.ForeignKey(Faction, verbose_name="Faction", on_delete=models.CASCADE)

    class Meta:
        verbose_name = "Transaction"
        verbose_name_plural = "Transactions"
        default_related_name = "transaction"
        ordering = ["id"]

    def __str__(self):
        return f"{self.reason} ({self.amount} Silver)"
