from django.urls import path

from apps.savegame import views

urlpatterns = [
    path("", views.SavegameListView.as_view(), name="savegame-list-view"),
    path("create/", views.SavegameCreateView.as_view(), name="savegame-create-view"),
]
