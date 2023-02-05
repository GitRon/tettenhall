from django.urls import path

from apps.warrior import views

urlpatterns = [
    path("warrior/<int:pk>", views.WarriorDetailView.as_view(), name="warrior-detail-view"),
    path(
        "warrior/<int:pk>/partial-update/<str:htmx_attribute>",
        views.WarriorWeaponUpdateView.as_view(),
        name="warrior-partial-update-view",
    ),
]
