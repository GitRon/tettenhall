from django.urls import path

from apps.marketplace import views

urlpatterns = [
    path("<int:pk>", views.MarketplaceView.as_view(), name="marketplace-view"),
]
