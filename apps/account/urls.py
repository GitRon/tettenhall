from django.urls import path

from apps.account import views

urlpatterns = [
    path("login/", views.LoginView.as_view(), name="login-view"),
    path("logout/", views.LogoutView.as_view(), {}, name="logout-view"),
    path("dashboard/", views.DashboardView.as_view(), name="dashboard-view"),
]
