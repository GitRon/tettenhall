from django.db.models import QuerySet
from django.views import generic

from apps.finance.models.transaction import Transaction
from apps.savegame.mixins import SavegameScopedQuerysetMixin
from apps.savegame.models.savegame import Savegame


class TransactionListView(SavegameScopedQuerysetMixin, generic.ListView):
    model = Transaction
    template_name = "finance/transaction_list.html"

    def get_queryset(self) -> QuerySet:
        return super().get_queryset().order_by("-id")

    def get_context_data(self, *, object_list=None, **kwargs) -> dict:
        context = super().get_context_data(object_list=object_list, **kwargs)

        # A user without an active savegame has no balance yet, and dereferencing it here answered
        # the whole page with a server error
        current_savegame: Savegame = Savegame.objects.get_current_savegame(user_id=self.request.user.id)
        context["current_balance"] = (
            Transaction.objects.current_balance(savegame_id=current_savegame.id) if current_savegame else 0
        )

        return context
