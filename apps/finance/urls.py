from django.urls import path

from apps.finance import views

urlpatterns = [
    path("<int:faction_id>", views.TransactionListView.as_view(), name="transaction-list-view"),
]
