import json
from http import HTTPStatus

from django.contrib import messages
from django.http import HttpResponse, HttpResponseRedirect
from django.shortcuts import get_object_or_404
from django.urls import reverse
from django.views import generic
from queuebie.runner import handle_message

from apps.common.utils import querydict_to_nested_dict
from apps.faction.models.faction import Faction
from apps.savegame.models.savegame import Savegame
from apps.skirmish.messages.commands.skirmish import FinishRound, StartDuel
from apps.skirmish.models import Warrior
from apps.skirmish.models.battle_history import BattleHistory
from apps.skirmish.models.skirmish import Skirmish
from apps.skirmish.projections.skirmish_participant import SkirmishParticipant


class SkirmishListView(generic.ListView):
    model = Skirmish
    template_name = "skirmish/skirmish_list.html"

    def get_queryset(self):
        current_savegame: Savegame = Savegame.objects.get_current_savegame(user_id=self.request.user.id)
        return super().get_queryset().for_savegame(savegame_id=current_savegame.id)


class SkirmishFightView(generic.DetailView):
    model = Skirmish
    template_name = "skirmish/skirmish_fight.html"

    def get_context_data(self, **kwargs):
        context = super().get_context_data(**kwargs)

        context["player_faction"] = self.object.player_faction
        context["non_player_faction"] = self.object.non_player_faction
        context["battle_log"] = self.object.battle_logs.all()

        return context

    def get(self, request, *args, **kwargs):
        skirmish = self.get_object()
        current_savegame = skirmish.player_faction.savegame
        if (
            self.model.objects.for_savegame(savegame_id=current_savegame.id)
            .has_started()
            .unresolved()
            .exclude(id=skirmish.id)
            .exists()
        ):
            messages.add_message(request, messages.WARNING, "Please finish your other skirmishes first.")
            return HttpResponseRedirect(reverse("skirmish:skirmish-list-view"))
        return super().get(request, *args, **kwargs)


class SkirmishFinishRoundView(generic.DetailView):
    model = Skirmish
    http_method_names = ("post",)
    object = None

    def post(self, request, *args, **kwargs):
        # TODO: make enemy warriors chose a skirmish action (in SkirmishFightView?)
        current_savegame: Savegame = Savegame.objects.get_current_savegame(user_id=self.request.user.id)

        self.object = (
            self.model.objects.filter(id=self.kwargs.get("pk"))
            .prefetch_related("player_warriors", "non_player_warriors")
            .first()
        )
        if not self.object:
            return HttpResponse(status=HTTPStatus.NOT_FOUND)
        skirmish_participants = querydict_to_nested_dict(querydict=request.POST, prefix="skirmish_participant")

        player_warrior_participants = []
        opposing_warrior_participants = []

        # Since we want objects in our event queue, we query all warriors once to avoid unnecessary db hits
        warrior_ids = []
        for participant_data in skirmish_participants.values():
            warrior_ids.append(participant_data["warrior_id"])
        warriors = Warrior.objects.filter(id__in=warrior_ids)

        for participant_data in skirmish_participants.values():
            if int(participant_data["faction_id"]) == self.object.player_faction.id:
                player_warrior_participants.append(
                    SkirmishParticipant(
                        warrior=warriors.get(id=participant_data["warrior_id"]),
                        skirmish_action=int(participant_data["skirmish_action"]),
                    )
                )
            elif int(participant_data["faction_id"]) == self.object.non_player_faction.id:
                opposing_warrior_participants.append(
                    SkirmishParticipant(
                        warrior=warriors.get(id=participant_data["warrior_id"]),
                        skirmish_action=int(participant_data["skirmish_action"]),
                    )
                )
            else:
                raise RuntimeError("Invalid faction ID in skirmish form.")

        # Ensure that all lists contain warriors
        if len(player_warrior_participants) == 0 or len(opposing_warrior_participants) == 0:
            return HttpResponse(status=HTTPStatus.BAD_REQUEST)

        # Start duel
        handle_message(
            StartDuel(
                skirmish=self.object,
                skirmish_participants_1=player_warrior_participants,
                skirmish_participants_2=opposing_warrior_participants,
            )
        )

        # Finish round
        handle_message(
            FinishRound(
                skirmish=self.object,
                month=current_savegame.current_month,
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

    def get_queryset(self):
        return super().get_queryset().filter(skirmish_id=self.kwargs.get("skirmish_id", -1))


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

        return context
