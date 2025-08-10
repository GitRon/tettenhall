from django.contrib import messages
from django.http import HttpResponse
from django.urls import reverse
from django.views import generic

from apps.finance.models import Transaction
from apps.savegame.models.savegame import Savegame
from apps.town.buildings.hall import Hall
from apps.town.models import Town


class TownUpgradeView(generic.DetailView):
    model = Town
    template_name = "town/town_upgrade.html"

    def get_object(self, queryset=...):
        return super().get_queryset().first()

    def get_queryset(self):
        current_savegame: Savegame = Savegame.objects.get_current_savegame(user_id=self.request.user.id)
        return Town.objects.for_savegame(savegame_id=current_savegame.id)


class UpgradeBuildingView(generic.DetailView):
    model = Town
    http_method_names = ("post",)

    def get_object(self, queryset=...):
        return super().get_queryset().first()

    def get_queryset(self):
        current_savegame: Savegame = Savegame.objects.get_current_savegame(user_id=self.request.user.id)
        return Town.objects.for_savegame(savegame_id=current_savegame.id)

    def post(self, request, *args, **kwargs):
        town = self.get_object()

        current_silver_balance = Transaction.objects.current_balance(savegame_id=town.faction.savegame_id)

        building_type = self.kwargs["building_type"]
        current_building_level = getattr(town, building_type)

        # TODO: make this generic based on "building_type"
        desired_building = Hall.get_building_by_type(hall_type=current_building_level)

        if current_building_level > 3:
            messages.add_message(request, messages.WARNING, "You already have the maximum building level.")
        if current_silver_balance < desired_building.BUILDING_COSTS:
            messages.add_message(request, messages.WARNING, "You don't have the silver to pay for the building.")
        else:
            # TODO: do this also via command?
            setattr(town, building_type, current_building_level + 1)
            town.save()
            # TODO: pay money via command

            messages.add_message(request, messages.SUCCESS, "Building upgraded.")

        response = HttpResponse()
        response["HX-Redirect"] = reverse("town:town-upgrade-view")
        return response
