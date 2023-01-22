from django.urls import path

from apps.item import views

urlpatterns = [
    path("<int:pk>/sell", views.ItemSellView.as_view(), name="item-sell-view"),
]
