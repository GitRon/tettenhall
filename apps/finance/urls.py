from django.urls import path

from apps.finance import views

urlpatterns = [
    path("", views.TransactionListView.as_view(), name="transaction-list-view"),
]
