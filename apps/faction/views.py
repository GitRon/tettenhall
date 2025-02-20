import json

from django.db.models import Sum
from django.shortcuts import render
from django.views import generic
from queuebie.runner import handle_message

from apps.faction.messages.commands.warrior import DraftWarriorFromFyrd
from apps.faction.models.faction import Faction
from apps.savegame.models.savegame import Savegame
from apps.skirmish.models.warrior import Warrior


class FactionDetailView(generic.DetailView):
    model = Faction
    template_name = "faction/faction_detail.html"

    def get_context_data(self, **kwargs):
        context = super().get_context_data(**kwargs)
        context["warrior_list"] = Warrior.objects.exclude_dead().filter_faction(faction_id=self.object.id)
        return context


class FactionItemListView(generic.DetailView):
    model = Faction
    template_name = "faction/item/components/item_list.html"


class FactionWarriorListView(generic.DetailView):
    model = Faction
    template_name = "faction/warrior/components/warrior_list.html"

    def get_context_data(self, **kwargs):
        context = super().get_context_data(**kwargs)
        context["warrior_list"] = Warrior.objects.exclude_dead().filter_faction(faction_id=self.object.id)
        return context


class FactionCapturedWarriorListView(generic.DetailView):
    model = Faction
    template_name = "faction/warrior/components/captured_warrior_list.html"


class DraftWarriorFromFyrdView(generic.DetailView):
    model = Faction
    http_method_names = ("post",)
    template_name = "faction/warrior/components/fyrd_card.html"

    def post(self, request, *args, **kwargs):
        obj = self.get_object()
        current_savegame: Savegame = Savegame.objects.get_current_savegame(user_id=self.request.user.id)

        handle_message(DraftWarriorFromFyrd(faction=obj, month=current_savegame.current_month))
        response = render(request, self.template_name, {"faction": obj})

        response["HX-Trigger"] = json.dumps(
            {
                "notification": "New Warrior drafted",
                "loadFactionWarriorList": "-",
                "loadFactionItemList": "-",
            }
        )

        return response


class MonthlyCostOverview(generic.DetailView):
    model = Faction
    template_name = "faction/faction/components/current_cost_card.html"

    def get_context_data(self, **kwargs):
        context = super().get_context_data(**kwargs)
        # Fetch current savegame record
        current_savegame: Savegame = Savegame.objects.get_current_savegame(user_id=self.request.user.id)

        player_faction = current_savegame.player_faction
        # TODO: put in manager
        context["monthly_salary_amount"] = (
            player_faction.warriors.exclude(condition=Warrior.ConditionChoices.CONDITION_DEAD).aggregate(
                sum_monthly_salary=Sum("monthly_salary")
            )["sum_monthly_salary"]
            or 0
        )
        return context
