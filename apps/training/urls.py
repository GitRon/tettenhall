from django.urls import path

from apps.training import views

urlpatterns = [
    path("", views.TrainingListView.as_view(), name="training-list-view"),
]
