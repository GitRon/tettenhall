from django.urls import path

from apps.account import views

urlpatterns = [
    path("dashboard/", views.DashboardView.as_view(), name="dashboard-view"),
]
