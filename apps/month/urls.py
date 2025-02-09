from django.urls import path

from apps.month import views

urlpatterns = [
    path("finish/", views.FinishMonthView.as_view(), name="finish-month-view"),
    path("player-month-log/", views.PlayerMonthLogListView.as_view(), name="player-month-log-list-view"),
    path(
        "player-month-log/<int:pk>/remove/",
        views.AcknowledgePlayerMonthLogView.as_view(),
        name="player-month-log-remove-view",
    ),
]
