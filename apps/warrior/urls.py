from django.urls import path

from apps.warrior import views

urlpatterns = [
    path("warrior/<int:pk>", views.WarriorDetailView.as_view(), name="warrior-detail-view"),
    path(
        "warrior/<int:pk>/captured/recruit/faction/<int:faction_id>",
        views.WarriorRecruitCapturedView.as_view(),
        name="warrior-recruit-captured-view",
    ),
    path(
        "warrior/<int:pk>/captured/enslave/faction/<int:faction_id>",
        views.WarriorEnslaveCapturedView.as_view(),
        name="warrior-enslave-captured-view",
    ),
    path(
        "warrior/<int:pk>/partial-update/<str:htmx_attribute>",
        views.WarriorWeaponUpdateView.as_view(),
        name="warrior-partial-update-view",
    ),
]
