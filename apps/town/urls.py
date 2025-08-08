from django.urls import path

from apps.town.views.town_upgrade import TownUpgradeView

urlpatterns = [
    path("", TownUpgradeView.as_view(), name="town-upgrade-view"),
]
