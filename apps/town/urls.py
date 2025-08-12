from django.urls import path

from apps.town.views.town_upgrade import TownUpgradeView, UpgradeBuildingView

urlpatterns = [
    path("", TownUpgradeView.as_view(), name="town-upgrade-view"),
    path("/building/upgrade/<str:building_type>", UpgradeBuildingView.as_view(), name="upgrade-building-view"),
]
