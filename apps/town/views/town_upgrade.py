from django.contrib import messages
from django.http import Http404, HttpResponse
from django.urls import reverse
from django.views import generic
from queuebie.runner import handle_message

from apps.finance.models import Transaction
from apps.savegame.mixins import PlayerFactionScopedQuerysetMixin
from apps.savegame.models.savegame import Savegame
from apps.town.buildings import BUILDINGS
from apps.town.messages.commands.town import UpgradeTownBuilding
from apps.town.models import Town


class PlayerTownMixin(PlayerFactionScopedQuerysetMixin):
    """
    Resolves the single town the current player owns.

    The URL carries no id, so the scoped queryset holds exactly that town - and nothing at all
    before the player has an active savegame with a faction, which both views used to walk into and
    answer with a server error.
    """

    def get_object(self, queryset=None) -> Town:
        # Going through "self" rather than "super()" is what keeps the scoping applied
        town = self.get_queryset().first()
        if town is None:
            raise Http404("The current savegame has no town.")

        return town


class TownUpgradeView(PlayerTownMixin, generic.DetailView):
    model = Town
    template_name = "town/town_upgrade.html"

    def get_context_data(self, **kwargs):
        town = self.object
        current_savegame: Savegame = Savegame.objects.get_current_savegame(user_id=self.request.user.id)

        has_already_built = town.last_constructed_building_at == current_savegame.current_month

        context = super().get_context_data(**kwargs)
        context.update({"has_already_built": has_already_built})

        building_list = []
        for building_type, building_class in BUILDINGS.items():
            current_level = getattr(town, building_type)
            # Capped at the maximum so the last level can still name a price instead of asking for a
            # variant above the largest one
            next_level = min(current_level + 1, building_class.get_max_level())

            building_list.append(
                {
                    "building_type": building_type,
                    "label": building_class.BUILDING_LABEL,
                    "level": current_level,
                    "level_display": getattr(town, f"get_{building_type}_display")(),
                    "max_level": building_class.get_max_level(),
                    "costs": building_class.get_building_by_type(building_type=next_level).BUILDING_COSTS,
                }
            )

        context.update({"building_list": building_list})

        return context


class UpgradeBuildingView(PlayerTownMixin, generic.DetailView):
    model = Town
    http_method_names = ("post",)

    def post(self, request, *args, **kwargs):
        # The building arrives as a free string from the URL, and its name is what "getattr" and the
        # handler's "setattr" address on the town. Without this lookup posting "faction_id" would
        # hand the town to another faction.
        building_type = self.kwargs["building_type"]
        if building_type not in BUILDINGS:
            raise Http404(f"Unknown building type: {building_type}")

        building_class = BUILDINGS[building_type]
        town = self.get_object()

        current_savegame: Savegame = Savegame.objects.get_current_savegame(user_id=self.request.user.id)
        current_silver_balance = Transaction.objects.current_balance(savegame_id=current_savegame.id)

        current_building_level = getattr(town, building_type)

        # The top level is the last one there is, so this has to stop there - asking for the next one
        # up would leave "get_building_by_type" without a match
        if current_building_level >= building_class.get_max_level():
            messages.add_message(request, messages.WARNING, "You already have the maximum building level.")

            # TODO: encapsulate this logic somewhere so we don't need to return this n times
            #  -> create validation service
            response = HttpResponse()
            response["HX-Redirect"] = reverse("town:town-upgrade-view")
            return response

        desired_building = building_class.get_building_by_type(building_type=current_building_level + 1)
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
