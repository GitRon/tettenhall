from django.contrib.auth.decorators import login_not_required
from django.urls import path

from apps.account import views

urlpatterns = [
    path("login/", login_not_required(views.LoginView.as_view()), name="login-view"),
    path("logout/", views.LogoutView.as_view(), {}, name="logout-view"),
    path("dashboard/", views.DashboardView.as_view(), name="dashboard-view"),
]
