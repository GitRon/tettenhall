import json

from django.http import HttpResponse
from django.shortcuts import get_object_or_404, redirect
from django.urls import reverse
from django.views import generic

from apps.core.event_loop.runner import handle_message
from apps.core.utils import convert_string_based_two_level_dict_to_dict
from apps.skirmish.forms import SkirmishWarriorRoundActionForm
from apps.skirmish.messages.commands.duel import StartDuel
from apps.skirmish.messages.events.duel import RoundFinished
from apps.skirmish.models.battle_history import BattleHistory
from apps.skirmish.models.faction import Faction
from apps.skirmish.models.skirmish import Skirmish, SkirmishWarriorRoundAction
from apps.skirmish.models.warrior import Warrior


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
            }
        )
        return response


"""
# todo
    -> nach gespräch mit marius
    duelservice:
    - synchrone events in klassenliste sammeln und dann im skirmishroundaggreate/service abfrühstücken und persistieren
    - SkirmishLog merkt sich die events und die eigentlichen texte werden on the fly generiert
    - repository für skirmish?
    - persistenz am ende der runde, dmait ich nicht mehrfach dinge speichern muss
    - speichern kann dann atomic werden
"""


class SkirmishRoundUpdateHtmxView(generic.DetailView):
    model = Skirmish
    template_name = "skirmish/skirmish/htmx/_round.html"


class BattleHistoryUpdateHtmxView(generic.ListView):
    model = BattleHistory
    template_name = "skirmish/battle_history/htmx/_report_box.html"


class FactionWarriorListUpdateHtmxView(generic.TemplateView):
    template_name = "skirmish/faction/htmx/_warrior_list.html"

    def get_context_data(self, **kwargs):
        skirmish = get_object_or_404(Skirmish, pk=self.kwargs.get("skirmish_id"))
        faction = get_object_or_404(Faction, pk=self.kwargs.get("faction_id"))

        context = super().get_context_data(**kwargs)
        # todo
        context["object_list"] = faction.warriors.all()
        context["is_player"] = skirmish.player_faction == faction
        # todo encapsulate properly as htmx snippet so we dont have this twice
        context["skirmish_action_form"] = {}
        for player_warrior in skirmish.player_warriors.all():
            context["skirmish_action_form"][player_warrior.id] = SkirmishWarriorRoundActionForm(
                faction_id=player_warrior.faction.id,
                warrior_id=player_warrior.id,
            )

        return context


class WarriorSkirmishActionCreateView(generic.CreateView):
    # todo kann weg
    model = SkirmishWarriorRoundAction
    form_class = SkirmishWarriorRoundActionForm

    def get_form_kwargs(self):
        kwargs = super().get_form_kwargs()
        kwargs["skirmish_id"] = self.kwargs.get("skirmish_id")
        kwargs["warrior_id"] = self.kwargs.get("warrior_id")
        kwargs["round"] = self.kwargs.get("round")
        return kwargs

    def post(self, request, *args, **kwargs):
        warrior = get_object_or_404(Warrior, pk=self.kwargs.get("warrior_id"))
        super().post(request, *args, **kwargs)
        return redirect(
            reverse(
                "skirmish:faction-warrior-list-update-htmx",
                kwargs={
                    "skirmish_id": self.kwargs.get("skirmish_id"),
                    "faction_id": warrior.faction.id,
                },
            )
        )

    def get_success_url(self):
        return None
