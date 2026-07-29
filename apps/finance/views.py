from django.db.models import QuerySet
from django.views import generic

from apps.finance.models.transaction import Transaction
from apps.savegame.mixins import PlayerFactionScopedQuerysetMixin
from apps.savegame.models.savegame import Savegame


class TransactionListView(PlayerFactionScopedQuerysetMixin, generic.ListView):
    model = Transaction
    template_name = "finance/transaction_list.html"

    def get_queryset(self) -> QuerySet:
        return super().get_queryset().order_by("-id")

    def get_context_data(self, *, object_list=None, **kwargs) -> dict:
        context = super().get_context_data(object_list=object_list, **kwargs)

        # A user without an active savegame has no balance yet, and dereferencing it here answered
        # the whole page with a server error. A savegame whose player faction is still to be created
        # owns no purse either, so there is nothing to ask the ledger about.
        current_savegame: Savegame = Savegame.objects.get_current_savegame(user_id=self.request.user.id)
        context["current_balance"] = (
            Transaction.objects.current_balance(faction_id=current_savegame.player_faction_id)
            if current_savegame and current_savegame.player_faction_id
            else 0
        )

        return context
