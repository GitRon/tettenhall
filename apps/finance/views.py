from django.views import generic

from apps.finance.models.transaction import Transaction


class TransactionListView(generic.ListView):
    model = Transaction
    template_name = "finance/transaction_list.html"

    def get_queryset(self):
        return super().get_queryset().for_user(user_id=self.request.user.id)
