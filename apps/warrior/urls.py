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
    # The warrior pk only: which roster he is sent away from is the player's, read off the savegame
    path("warrior/<int:pk>/dismiss", views.DismissWarriorView.as_view(), name="warrior-dismiss-view"),
    path(
        "warrior/<int:pk>/partial-update/<str:htmx_attribute>",
        views.WarriorWeaponUpdateView.as_view(),
        name="warrior-partial-update-view",
    ),
]
