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
from apps.skirmish.choices.skirmish_action import SkirmishActionChoices
from apps.skirmish.messages.commands.skirmish import FinishRound, StartDuel
from apps.skirmish.models.battle_history import BattleHistory
from apps.skirmish.models.skirmish import Skirmish
from apps.skirmish.projections.skirmish_participant import SkirmishParticipant
from apps.skirmish.services.skirmish.skirmish_participants import (
    SkirmishParticipantBuilderService,
    UnknownSkirmishParticipantError,
)


class OccupiableSideMixin:
    """
    Puts the side of this fight whose town can now simply be ridden into on the context.

    The signal that matters most about an occupation comes off the fight that opened the window, and
    that is here: the last defender falling is what makes the town takeable, and the player is looking
    straight at it. Read at render time from "occupiable_by" rather than recorded anywhere, so it goes
    away by itself once the month turns and the rival's men are back on their feet.

    Who won is deliberately not asked. The player's own faction is not in "rivals_in_play" and a side
    with anyone healthy left is not occupiable, so at most one of the two sides can ever come back -
    and a mutual wipeout that left the player's own war band flattened still offers the right one.

    Shared by the fight page and the htmx partial it swaps in, which render the same template: the
    prompt has to appear on the "updateFightButton" trigger that follows the winning round, not only
    on a reload.
    """

    def get_occupiable_faction(self, *, skirmish) -> Faction | None:
        current_savegame: Savegame = Savegame.objects.get_current_savegame(user_id=self.request.user.id)
        if current_savegame is None or current_savegame.player_faction is None:
            return None

        return (
            Faction.objects.occupiable_by(player_faction=current_savegame.player_faction)
            .filter(id__in=(skirmish.attacking_faction_id, skirmish.defending_faction_id))
            .first()
        )


class SkirmishListView(SavegameScopedQuerysetMixin, generic.ListView):
    model = Skirmish
    template_name = "skirmish/skirmish_list.html"


class SkirmishFightView(OccupiableSideMixin, SavegameScopedQuerysetMixin, generic.DetailView):
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
        context["occupiable_faction"] = self.get_occupiable_faction(skirmish=self.object)

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

    def _player_commanded_his_whole_side(
        self,
        *,
        attacking_participants: list[SkirmishParticipant],
        defending_participants: list[SkirmishParticipant],
    ) -> bool:
        """
        Whether every healthy warrior the player commands was given an action.

        Asked of both sides without knowing which is his: the side he does not command was built from
        the roster and therefore covers itself by construction, so testing both costs nothing and
        needs no second copy of the "which side is the player's" question.
        """
        for roster, participants in (
            (self.object.attacking_warriors.all(), attacking_participants),
            (self.object.defending_warriors.all(), defending_participants),
        ):
            commanded = {participant.warrior.id for participant in participants}
            if any(warrior.is_healthy and warrior.id not in commanded for warrior in roster):
                return False

        return True

    def post(self, request, *args, **kwargs):
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

        # Every value here arrives in the request body, so anything missing, non-numeric or naming an
        # action that does not exist is bad input rather than a server error. Without the membership
        # test an unknown number reached "get_service_by_attack_action" and raised there, answering 500
        # to input this very block means to refuse. The posted "faction_id" is deliberately not read:
        # which side a warrior fights on comes from the skirmish's own rosters, since a posted one can
        # lie and "warrior.faction" changes the moment a captive is recruited.
        try:
            participants = [
                (int(participant_data["warrior_id"]), SkirmishActionChoices(int(participant_data["skirmish_action"])))
                for participant_data in skirmish_participants.values()
            ]
        except KeyError, ValueError:
            return HttpResponse(status=HTTPStatus.BAD_REQUEST)

        # The enemy's actions are decided here rather than read off the request: his card used to post
        # the AI's choice back in a field the player could edit. The service takes the whole side, so
        # leaving an enemy out of the post no longer leaves him out of the fight either.
        try:
            attacking_participants, defending_participants = SkirmishParticipantBuilderService(
                skirmish=self.object,
                participants=participants,
                player_faction_id=current_savegame.player_faction_id if current_savegame else None,
            ).process()
        except UnknownSkirmishParticipantError:
            # A warrior id naming someone who is not fighting this skirmish
            return HttpResponse(status=HTTPStatus.BAD_REQUEST)

        # A side with nobody in it is not a fight, and the pairing handler picks a random opponent from
        # each list - an empty one raises there. This used to prove both sides had been *posted*; now
        # that only the player's side is, it proves both rosters actually field somebody healthy.
        if len(attacking_participants) == 0 or len(defending_participants) == 0:
            return HttpResponse(status=HTTPStatus.BAD_REQUEST)

        # And the player has to have commanded every one of his own healthy warriors, which the check
        # above no longer implies: leaving a man out of the post used to shrink the side, and would
        # now silently field him against nobody.
        if not self._player_commanded_his_whole_side(
            attacking_participants=attacking_participants, defending_participants=defending_participants
        ):
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


class SkirmishFightButtonUpdateHtmxView(OccupiableSideMixin, SavegameScopedQuerysetMixin, generic.DetailView):
    model = Skirmish
    template_name = "skirmish/skirmish/htmx/_fight_button.html"

    def get_context_data(self, **kwargs):
        context = super().get_context_data(**kwargs)
        # The swap that follows the winning round renders this template on its own, so without this
        # the prompt would only ever appear on a reload of the page the player has just finished with
        context["occupiable_faction"] = self.get_occupiable_faction(skirmish=self.object)
        return context


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
