import json

from django.db.models import Sum
from django.shortcuts import render
from django.views import generic

from apps.core.event_loop.runner import handle_message
from apps.faction.messages.commands.warrior import DraftWarriorFromFyrd
from apps.faction.models.faction import Faction
from apps.skirmish.models.warrior import Warrior


class FactionDetailView(generic.DetailView):
    model = Faction
    template_name = "faction/faction_detail.html"


class FactionItemListView(generic.DetailView):
    model = Faction
    template_name = "faction/item/components/item_list.html"


class FactionWarriorListView(generic.DetailView):
    model = Faction
    template_name = "faction/warrior/components/warrior_list.html"


class FactionCapturedWarriorListView(generic.DetailView):
    model = Faction
    template_name = "faction/warrior/components/captured_warrior_list.html"


class DraftWarriorFromFyrdView(generic.DetailView):
    model = Faction
    http_method_names = ("post",)
    template_name = "faction/warrior/components/fyrd_card.html"

    def post(self, request, *args, **kwargs):
        obj = self.get_object()

        handle_message(DraftWarriorFromFyrd(DraftWarriorFromFyrd.Context(faction=obj)))
        response = render(request, self.template_name, {"faction": obj})

        response["HX-Trigger"] = json.dumps(
            {
                "notification": "New Warrior drafted",
                "loadFactionWarriorList": "-",
            }
        )

        return response


class WeeklyCostOverview(generic.DetailView):
    model = Faction
    template_name = "faction/faction/components/current_cost_card.html"

    def get_context_data(self, **kwargs):
        context = super().get_context_data(**kwargs)
        # todo player faction is still static here
        player_faction = Faction.objects.get(id=2)
        context["weekly_salary_amount"] = (
            player_faction.warriors.exclude(condition=Warrior.ConditionChoices.CONDITION_DEAD)
            .aggregate(sum_weekly_salary=Sum("weekly_salary"))
            .get("sum_weekly_salary", 0.0)
        )
        return context
