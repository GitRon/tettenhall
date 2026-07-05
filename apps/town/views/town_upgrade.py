from django.contrib import messages
from django.http import HttpResponse
from django.urls import reverse
from django.views import generic
from queuebie.runner import handle_message

from apps.finance.models import Transaction
from apps.savegame.models.savegame import Savegame
from apps.town.buildings.hall import Hall
from apps.town.messages.commands.town import UpgradeTownBuilding
from apps.town.models import Town


class TownUpgradeView(generic.DetailView):
    model = Town
    template_name = "town/town_upgrade.html"

    def get_object(self, queryset=...):
        return super().get_queryset().first()

    def get_queryset(self):
        current_savegame: Savegame = Savegame.objects.get_current_savegame(user_id=self.request.user.id)
        return Town.objects.for_savegame(savegame_id=current_savegame.id)

    def get_context_data(self, **kwargs):
        town = self.get_object()
        current_savegame: Savegame = Savegame.objects.get_current_savegame(user_id=self.request.user.id)

        has_already_built = town.last_constructed_building_at == current_savegame.current_month

        context = super().get_context_data(**kwargs)
        context.update({"has_already_built": has_already_built})

        building_costs_hall = Hall.get_building_by_type(
            building_type=min(town.hall + 1, Town.HallChoices.HALL_LARGE)
        ).BUILDING_COSTS
        # TODO: add building costs
        building_costs_weaponsmith = 0
        building_costs_marketplace = 0
        building_costs_sanctuary = 0

        context.update(
            {
                "building_costs_hall": building_costs_hall,
                "building_costs_weaponsmith": building_costs_weaponsmith,
                "building_costs_marketplace": building_costs_marketplace,
                "building_costs_sanctuary": building_costs_sanctuary,
            }
        )

        return context


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

        current_savegame: Savegame = Savegame.objects.get_current_savegame(user_id=self.request.user.id)
        current_silver_balance = Transaction.objects.current_balance(savegame_id=town.faction.savegame_id)

        building_type = self.kwargs["building_type"]
        current_building_level = getattr(town, building_type)

        if current_building_level > 3:
            messages.add_message(request, messages.WARNING, "You already have the maximum building level.")

            # TODO: encapsulate this logic somewhere so we don't need to return this n times
            #  -> create validation service
            response = HttpResponse()
            response["HX-Redirect"] = reverse("town:town-upgrade-view")
            return response

        # TODO: make this generic based on "building_type"
        desired_building = Hall.get_building_by_type(building_type=current_building_level + 1)
        if current_silver_balance < desired_building.BUILDING_COSTS:
            messages.add_message(request, messages.WARNING, "You don't have the silver to pay for the building.")

            response = HttpResponse()
            response["HX-Redirect"] = reverse("town:town-upgrade-view")
            return response

        if town.last_constructed_building_at == current_savegame.current_month:
            messages.add_message(request, messages.WARNING, "You've already commissioned a building this month.")

            response = HttpResponse()
            response["HX-Redirect"] = reverse("town:town-upgrade-view")
            return response

        handle_message(
            UpgradeTownBuilding(
                town=town,
                faction=town.faction,
                building_type=building_type,
                new_level=current_building_level + 1,
                costs=desired_building.BUILDING_COSTS,
                month=current_savegame.current_month,
            )
        )
        messages.add_message(request, messages.SUCCESS, "Building upgraded.")

        response = HttpResponse()
        response["HX-Redirect"] = reverse("town:town-upgrade-view")
        return response
