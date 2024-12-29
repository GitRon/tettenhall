from django.views import generic

from apps.finance.models.transaction import Transaction
from apps.savegame.models.savegame import Savegame


class TransactionListView(generic.ListView):
    model = Transaction
    template_name = "finance/transaction_list.html"

    def get_queryset(self):
        current_savegame: Savegame = Savegame.objects.get_current_savegame(user_id=self.request.user.id)
        return super().get_queryset().for_savegame(savegame_id=current_savegame.id)
