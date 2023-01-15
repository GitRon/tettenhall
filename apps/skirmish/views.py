import json

from django.http import HttpResponse
from django.shortcuts import get_object_or_404
from django.views import generic

from apps.core.event_loop.runner import handle_message
from apps.core.utils import convert_string_based_two_level_dict_to_dict
from apps.skirmish.forms import SkirmishWarriorRoundActionForm
from apps.skirmish.messages.commands.skirmish import StartDuel
from apps.skirmish.messages.events.skirmish import RoundFinished
from apps.skirmish.models.battle_history import BattleHistory
from apps.skirmish.models.faction import Faction
from apps.skirmish.models.skirmish import Skirmish


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

        context["skirmish_action_form"] = {}
        for player_warrior in self.object.player_warriors.all():
            context["skirmish_action_form"][player_warrior.id] = SkirmishWarriorRoundActionForm(
                faction_id=player_warrior.faction.id,
                warrior_id=player_warrior.id,
            )

        return context


class SkirmishFinishRoundView(generic.DetailView):
    model = Skirmish
    http_method_names = ("post",)
    object = None

    # todo fixme use formset/something different

    def post(self, request, *args, **kwargs):
        self.object = self.get_object()
        # todo datenübergabe sauberer gestalten
        converted_data = convert_string_based_two_level_dict_to_dict(request.POST)

        # Start duel
        handle_message(
            StartDuel.generator(
                context_data={
                    "skirmish": self.object,
                    "warrior_list_1": converted_data["warrior-fight-action"][self.object.player_faction.id],
                    "warrior_list_2": converted_data["warrior-fight-action"][self.object.non_player_faction.id],
                }
            )
        )

        # Finish round
        # todo add command if one list is dead, that skirmish will be closed
        handle_message(
            RoundFinished.generator(
                context_data={
                    "skirmish": self.object,
                }
            )
        )

        response = HttpResponse()
        response["HX-Trigger"] = json.dumps(
            {
                "battleReportUpdate": "-",
                "notification": "Round finished",
                "updateFactionWarriorList": "-",
                "updateSkirmishRound": "-",
                "updateFightButton": "-",
            }
        )
        return response


class SkirmishRoundUpdateHtmxView(generic.DetailView):
    model = Skirmish
    template_name = "skirmish/skirmish/htmx/_round.html"


class SkirmishFightButtonUpdateHtmxView(generic.DetailView):
    model = Skirmish
    template_name = "skirmish/skirmish/htmx/_fight_button.html"


class BattleHistoryUpdateHtmxView(generic.ListView):
    model = BattleHistory
    template_name = "skirmish/battle_history/htmx/_report_box.html"


class FactionWarriorListUpdateHtmxView(generic.TemplateView):
    template_name = "skirmish/faction/htmx/_warrior_list.html"

    def get_context_data(self, **kwargs):
        skirmish = get_object_or_404(Skirmish, pk=self.kwargs.get("skirmish_id"))
        faction = get_object_or_404(Faction, pk=self.kwargs.get("faction_id"))

        context = super().get_context_data(**kwargs)
        if faction == skirmish.player_faction:
            context["object_list"] = skirmish.player_warriors.all()
        else:
            context["object_list"] = skirmish.non_player_warriors.all()
        context["is_player"] = skirmish.player_faction == faction
        # todo encapsulate properly as htmx snippet so we don't have this twice
        context["skirmish_action_form"] = {}
        for player_warrior in skirmish.player_warriors.all():
            context["skirmish_action_form"][player_warrior.id] = SkirmishWarriorRoundActionForm(
                faction_id=player_warrior.faction.id,
                warrior_id=player_warrior.id,
            )

        return context
