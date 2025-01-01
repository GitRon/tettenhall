from django.urls import path

from apps.marketplace import views

urlpatterns = [
    path("<int:pk>", views.MarketplaceView.as_view(), name="marketplace-view"),
    path("<int:pk>/htmx/item", views.MarketplaceItemListView.as_view(), name="marketplace-item-list-htmx"),
]
