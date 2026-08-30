import json
from http import HTTPStatus

from django.contrib import messages
from django.db.models import QuerySet
from django.http import HttpResponse, HttpResponseRedirect
from django.shortcuts import get_object_or_404
from django.urls import reverse
from django.views import generic
from queuebie.runner import handle_message

from apps.common.utils import querydict_to_nested_dict
from apps.faction.models.faction import Faction
from apps.savegame.mixins import RunningSavegameRequiredMixin, SavegameScopedQuerysetMixin
from apps.savegame.models.savegame import Savegame
from apps.savegame.services.current_savegame import get_current_savegame_for_request
from apps.skirmish.messages.commands.skirmish import FinishRound, StartDuel
from apps.skirmish.models.battle_history import BattleHistory
from apps.skirmish.models.skirmish import Skirmish
from apps.skirmish.projections.skirmish_participant import SkirmishParticipant


class SkirmishListView(SavegameScopedQuerysetMixin, generic.ListView):
    model = Skirmish
    template_name = "skirmish/skirmish_list.html"


class SkirmishFightView(SavegameScopedQuerysetMixin, generic.DetailView):
    model = Skirmish
    template_name = "skirmish/skirmish_fight.html"
    object = None
    current_savegame = None

    def get_context_data(self, **kwargs):
        context = super().get_context_data(**kwargs)

        # The skirmish names its two sides by role, so whether a side is the player's - and therefore
        # whether its warrior cards let the human pick an action instead of showing the AI's decision -
        # is decided here, against the savegame. At most one of the two is True: a savegame that has no
        # player faction yet makes both False rather than guessing at a side. Both the savegame and the
        # skirmish were resolved by get() below, which is the only caller
        player_faction_id = self.current_savegame.player_faction_id

        context["attacking_faction"] = self.object.attacking_faction
        context["defending_faction"] = self.object.defending_faction
        context["attacker_is_player"] = self.object.attacking_faction_id == player_faction_id
        context["defender_is_player"] = self.object.defending_faction_id == player_faction_id
        context["battle_log"] = self.object.battle_logs.all()

        return context

    def get(self, request, *args, **kwargs):
        # Both are resolved once here and kept on the view. Handing off to super().get() instead would
        # fetch the same skirmish a second time - and its own scoped get_queryset() re-reads the
        # savegame to do it - so the two lines it saves cost three queries per render.
        # Straight from the savegame rather than from a side of the skirmish: the scoped queryset
        # already guarantees this skirmish belongs to the current savegame, and which of its sides is
        # the player's is no longer the row's business
        self.object = self.get_object()
        self.current_savegame: Savegame = get_current_savegame_for_request(request=request)

        if (
            self.model.objects.for_savegame(savegame_id=self.current_savegame.id)
            .has_started()
            .unresolved()
            .exclude(id=self.object.id)
            .exists()
        ):
            messages.add_message(request, messages.WARNING, "Please finish your other skirmishes first.")
            return HttpResponseRedirect(reverse("skirmish:skirmish-list-view"))

        return self.render_to_response(self.get_context_data(object=self.object))


class SkirmishFinishRoundView(RunningSavegameRequiredMixin, SavegameScopedQuerysetMixin, generic.DetailView):
    model = Skirmish
    http_method_names = ("post",)
    object = None

    def post(self, request, *args, **kwargs):
        # TODO: make enemy warriors chose a skirmish action (in SkirmishFightView?)
        current_savegame: Savegame = get_current_savegame_for_request(request=self.request)

        # Through the scoped queryset, otherwise the id from the URL would be enough to fight
        # another player's skirmish
        self.object = (
            self.get_queryset()
            .filter(id=self.kwargs.get("pk"))
            .prefetch_related("attacking_warriors", "defending_warriors")
            .first()
        )
        if not self.object:
            return HttpResponse(status=HTTPStatus.NOT_FOUND)
        skirmish_participants = querydict_to_nested_dict(querydict=request.POST, prefix="skirmish_participant")

        attacking_participants = []
        defending_participants = []

        # Every value here arrives in the request body, so anything missing or non-numeric is bad
        # input rather than a server error. The posted "faction_id" is deliberately not read: see
        # the side assignment below.
        try:
            participants = [
                (int(participant_data["warrior_id"]), int(participant_data["skirmish_action"]))
                for participant_data in skirmish_participants.values()
            ]
        except KeyError, ValueError:
            return HttpResponse(status=HTTPStatus.BAD_REQUEST)

        # Which side a warrior fights on comes from this skirmish's own rosters. Not from the posted
        # "faction_id", which is client-supplied - naming the opposing faction there put a warrior into
        # the other side's line-up, attacking his own side. And not from "warrior.faction"
        # either, which is what the template fills that field with: it changes the moment a captive
        # is recruited, so it disagrees with the roster the warrior actually fights in.
        # Both relations are prefetched above, so this costs no extra queries, and keying by id
        # means a warrior listed twice cannot produce a duplicate-row lookup error.
        attacking_roster = {warrior.id: warrior for warrior in self.object.attacking_warriors.all()}
        defending_roster = {warrior.id: warrior for warrior in self.object.defending_warriors.all()}

        for warrior_id, skirmish_action in participants:
            if warrior_id in attacking_roster:
                warrior, side = attacking_roster[warrior_id], attacking_participants
            elif warrior_id in defending_roster:
                warrior, side = defending_roster[warrior_id], defending_participants
            else:
                # A warrior id naming someone who is not fighting this skirmish
                return HttpResponse(status=HTTPStatus.BAD_REQUEST)

            side.append(SkirmishParticipant(warrior=warrior, skirmish_action=skirmish_action))

        # Ensure that all lists contain warriors
        if len(attacking_participants) == 0 or len(defending_participants) == 0:
            return HttpResponse(status=HTTPStatus.BAD_REQUEST)

        # Start duel
        handle_message(
            StartDuel(
                skirmish=self.object,
                skirmish_participants_1=attacking_participants,
                skirmish_participants_2=defending_participants,
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


class SkirmishRoundUpdateHtmxView(SavegameScopedQuerysetMixin, generic.DetailView):
    model = Skirmish
    template_name = "skirmish/skirmish/htmx/_round.html"


class SkirmishFightButtonUpdateHtmxView(SavegameScopedQuerysetMixin, generic.DetailView):
    model = Skirmish
    template_name = "skirmish/skirmish/htmx/_fight_button.html"


class BattleHistoryUpdateHtmxView(SavegameScopedQuerysetMixin, generic.ListView):
    model = BattleHistory
    template_name = "skirmish/battle_history/htmx/_report_box.html"

    def get_queryset(self) -> QuerySet:
        # The mixin scopes to the current savegame, otherwise any skirmish id from the URL would
        # expose another player's battle history
        return super().get_queryset().filter(skirmish_id=self.kwargs.get("skirmish_id", -1))


class FactionWarriorListUpdateHtmxView(generic.TemplateView):
    template_name = "skirmish/faction/htmx/_warrior_list.html"

    def get_context_data(self, **kwargs):
        # Both ids arrive in the URL: the skirmish has to belong to the current savegame, and the
        # faction has to be one of the two fighting it - otherwise an unrelated faction would fall
        # through to the defending branch below and be shown those warriors
        current_savegame: Savegame = get_current_savegame_for_request(request=self.request)
        skirmish = get_object_or_404(
            Skirmish.objects.for_savegame(savegame_id=current_savegame.id if current_savegame else None),
            pk=self.kwargs.get("skirmish_id"),
        )
        faction = get_object_or_404(
            Faction.objects.filter(id__in=(skirmish.attacking_faction_id, skirmish.defending_faction_id)),
            pk=self.kwargs.get("faction_id"),
        )

        context = super().get_context_data(**kwargs)
        if faction.pk == skirmish.attacking_faction_id:
            context["object_list"] = skirmish.attacking_warriors.all()
        else:
            context["object_list"] = skirmish.defending_warriors.all()
        # Which roster to show is the skirmish's business, but whether the human commands it is the
        # savegame's: being the attacker no longer means being the player
        context["is_player"] = faction.pk == current_savegame.player_faction_id

        return context
