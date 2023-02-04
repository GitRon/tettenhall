from django.urls import path

from apps.week import views

urlpatterns = [
    path("finish/", views.FinishWeekView.as_view(), name="finish-week-view"),
    path("player-week-log/", views.PlayerWeekLogListView.as_view(), name="player-week-log-list-view"),
    path(
        "player-week-log/<int:pk>/remove/",
        views.AcknowledgePlayerWeekLogView.as_view(),
        name="player-week-log-remove-view",
    ),
]
