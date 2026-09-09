from django.db.models import QuerySet
from django.views import generic

from apps.warband.finance.models.transaction import Transaction
from apps.warband.savegame.mixins import PlayerFactionScopedQuerysetMixin


class TransactionListView(PlayerFactionScopedQuerysetMixin, generic.ListView):
    model = Transaction
    template_name = "finance/transaction_list.html"

    def get_queryset(self) -> QuerySet:
        return super().get_queryset().order_by("-id")

    # "current_balance" comes from the globally registered get_current_balance context processor,
    # the same number the navbar shows - computing it here again just made the two drift apart.
