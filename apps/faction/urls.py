from django.urls import path

from apps.faction import views

urlpatterns = [
    path("<int:pk>/htmx/item", views.FactionItemListView.as_view(), name="faction-item-list-htmx"),
    path("<int:pk>/htmx/warrior", views.FactionWarriorListView.as_view(), name="faction-warrior-list-htmx"),
    path("<int:pk>", views.FactionDetailView.as_view(), name="faction-detail-view"),
]
