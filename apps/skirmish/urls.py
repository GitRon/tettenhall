from django.urls import path

from apps.skirmish import views

urlpatterns = [
    path("", views.SkirmishListView.as_view(), name="skirmish-list-view"),
    path("<int:pk>/", views.SkirmishFightView.as_view(), name="skirmish-fight-view"),
    path(
        "<int:pk>/finish-round/",
        views.SkirmishFinishRoundView.as_view(),
        name="skirmish-finish-round-view",
    ),
    path(
        "battle_log/update/",
        views.BattleLogUpdateHtmxView.as_view(),
        name="battle-log-update-htmx",
    ),
    path(
        "<int:skirmish_id>/faction/<int:faction_id>/warrior-list/update/",
        views.FactionWarriorListUpdateHtmxView.as_view(),
        name="faction-warrior-list-update-htmx",
    ),
]
