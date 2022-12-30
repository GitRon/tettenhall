import json
import re

from django.http import HttpResponse
from django.shortcuts import get_object_or_404
from django.views import generic

from apps.skirmish.models.battle_log import BattleLog
from apps.skirmish.models.faction import Faction
from apps.skirmish.models.skirmish import Skirmish
from apps.skirmish.models.warrior import Warrior
from apps.skirmish.services.duel import DuelService


class SkirmishListView(generic.ListView):
    model = Skirmish
    template_name = "skirmish/skirmish_list.html"


class SkirmishFightView(generic.DetailView):
    model = Skirmish
    template_name = "skirmish/skirmish_fight.html"

    def get_context_data(self, **kwargs):
        context = super().get_context_data(**kwargs)

        context["player_faction"] = self.object.player_faction
        context["non_player_faction"] = self.object.non_player_faction
        context["battle_log"] = self.object.battle_logs.all()

        # fixme temp
        # service = FightService(
        #     skirmish=self.object,
        #     party_1=context["player_faction"].warriors.all(),
        #     party_2=context["non_player_faction"].warriors.all(),
        # )
        # service.process()

        return context


class SkirmishFinishRoundView(generic.DetailView):
    model = Skirmish
    http_method_names = ("post",)
    object = None

    # todo fixme use formset/something different

    def post(self, request, *args, **kwargs):
        self.object = self.get_object()
        # todo hier muss ich vorher noch die pärchen aufteilen, aktuell kämpfen hier noch alle
        print(request.POST)
        fighter_list = []
        for key, value in request.POST.items():
            if "warrior-action" in key:
                try:
                    warrior_id = re.search("\[(\d+)\]$", key).group(1)
                except IndexError:
                    raise ValueError("Malformed data sent.")
                action_id = value
                print(warrior_id, action_id)
                fighter_list.append({"warrior_id": warrior_id, "action_id": action_id})

        warrior_1 = get_object_or_404(Warrior, pk=fighter_list[0]["warrior_id"])
        warrior_2 = get_object_or_404(Warrior, pk=fighter_list[1]["warrior_id"])

        # Calculate fight
        service = DuelService(
            skirmish=self.object,
            warrior_1=warrior_1,
            warrior_2=warrior_2,
            action_1=fighter_list[0]["action_id"],
            action_2=fighter_list[1]["action_id"],
        )
        service.process()

        response = HttpResponse()
        response["HX-Trigger"] = json.dumps(
            {
                "battleReportUpdate": "-",
                "notification": "Round finished",
                "updateFactionWarriorList": "-",
            }
        )
        return response


class BattleLogUpdateHtmxView(generic.ListView):
    model = BattleLog
    template_name = "skirmish/battle_log/htmx/_report_box.html"


class FactionWarriorListUpdateHtmxView(generic.TemplateView):
    template_name = "skirmish/faction/htmx/_warrior_list.html"

    def get_context_data(self, **kwargs):
        skirmish = get_object_or_404(Skirmish, pk=self.kwargs.get("skirmish_id"))
        faction = get_object_or_404(Faction, pk=self.kwargs.get("faction_id"))

        context = super().get_context_data(**kwargs)
        context["object_list"] = faction.warriors.all()
        context["is_player"] = skirmish.player_faction == faction
        return context
