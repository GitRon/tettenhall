from django.urls import path

from apps.quest import views

urlpatterns = [
    path("list", views.QuestListView.as_view(), name="quest-list-view"),
    path("<int:pk>/accept", views.QuestAcceptView.as_view(), name="quest-accept-view"),
    path("<int:pk>", views.QuestDetailView.as_view(), name="quest-detail-view"),
]
