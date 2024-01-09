from django.urls import path

from apps.quest import views

urlpatterns = [
    path("<int:pk>/accept", views.QuestAcceptView.as_view(), name="quest-accept-view"),
]
