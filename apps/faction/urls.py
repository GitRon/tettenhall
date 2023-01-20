from django.urls import path

from apps.faction import views

urlpatterns = [
    path("<int:pk>", views.FactionDetailView.as_view(), name="faction-detail-view"),
]
