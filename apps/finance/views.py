from django.views import generic

from apps.finance.models.transaction import Transaction
from apps.savegame.models.savegame import Savegame


class TransactionListView(generic.ListView):
    model = Transaction
    template_name = "finance/transaction_list.html"
    current_savegame: Savegame = None

    def dispatch(self, request, *args, **kwargs):
        # TODO: put this in mixin?
        self.current_savegame: Savegame = Savegame.objects.get_current_savegame(user_id=self.request.user.id)
        return super().dispatch(request, *args, **kwargs)

    def get_queryset(self):
        return super().get_queryset().for_savegame(savegame_id=self.current_savegame.id).order_by("-id")

    def get_context_data(self, *, object_list=None, **kwargs):
        context = super().get_context_data(object_list=object_list, **kwargs)
        context["current_balance"] = Transaction.objects.current_balance(savegame_id=self.current_savegame.id)
        return context
