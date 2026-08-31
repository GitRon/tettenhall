import json
from http import HTTPStatus

from django.http import Http404, HttpResponse
from django.shortcuts import get_object_or_404, render
from django.views import generic
from queuebie.runner import handle_message

from apps.faction.models.faction import Faction
from apps.savegame.mixins import (
    PlayerFactionScopedQuerysetMixin,
    RunningSavegameRequiredMixin,
    SavegameScopedQuerysetMixin,
)
from apps.savegame.models.savegame import Savegame
from apps.savegame.services.current_savegame import get_current_savegame_for_request
from apps.skirmish.models.warrior import Warrior
from apps.warrior.forms.warrior import WarriorForm
from apps.warrior.messages.commands.warrior import EnslaveCapturedWarrior, RecruitCapturedWarrior


class WarriorDetailView(SavegameScopedQuerysetMixin, generic.DetailView):
    model = Warrior
    template_name = "warrior/warrior_detail.html"

    def get_context_data(self, **kwargs) -> dict:
        context = super().get_context_data(**kwargs)
        # This page is where a rival card's "Detail" link leads, so it has to withhold the gear that
        # card withholds - otherwise hiding it one screen earlier only costs the player a click.
        #
        # Asked as "may the player see this man's gear", not "is he in the player's faction": the two
        # come apart for everybody carrying no faction at all. His own prisoners and the mercenaries
        # standing in his own pub are faction-less, and the pub card already advertises the weapon it
        # is charging him for - so a faction test would have hidden, one click later, what the town
        # square had just shown him.
        current_savegame = get_current_savegame_for_request(request=self.request)
        player_faction = current_savegame.player_faction if current_savegame else None
        context["can_see_gear"] = player_faction is not None and (
            self.object.faction_id == player_faction.id
            or player_faction.captured_warriors.filter(id=self.object.id).exists()
            or player_faction.available_mercenaries.filter(id=self.object.id).exists()
        )
        return context


class WarriorWeaponUpdateView(PlayerFactionScopedQuerysetMixin, generic.UpdateView):
    # Changing what a warrior carries is a write, and being in the player's savegame is not enough:
    # a rival's men are in it too, and the URL was all it took to re-arm them
    model = Warrior
    form_class = WarriorForm
    template_name = "warrior/components/warrior_field_edit.html"
    object = None
    htmx_field = None

    def dispatch(self, request, *args, **kwargs):
        # The attribute is a free URL segment, and the form raises on anything it doesn't render -
        # which is a 404, not a server error
        self.htmx_field = kwargs.get("htmx_attribute")
        if self.htmx_field not in WarriorForm.Meta.fields:
            raise Http404("Unknown warrior attribute.")

        return super().dispatch(request, *args, **kwargs)

    def get_form_kwargs(self):
        kwargs = super().get_form_kwargs()
        kwargs["htmx_field"] = self.htmx_field
        return kwargs

    def form_valid(self, form):
        self.object = form.save()
        return render(self.request, "warrior/components/warrior_field_display.html", self.get_context_data())

    def get_context_data(self, **kwargs):
        context = super().get_context_data(**kwargs)
        context["object"] = self.object
        context["attribute"] = self.htmx_field
        context["field_value"] = getattr(self.object, self.htmx_field)
        return context


class CapturedWarriorActionMixin(SavegameScopedQuerysetMixin):
    """
    Resolves the player's own faction as the one holding a captured warrior.

    Two facts have to be verified, and the savegame is not enough for either. The faction id arrives in
    the URL, so it could name a rival of this very savegame - and a rival is a faction the player may
    not act for: recruiting a rival's captive staffs the rival's war band for free, and enslaving one
    pays the rival for his own prisoner. And "remove_captive()" is a silent no-op for a warrior that was
    never captured, so without the membership check a player could enslave his own warriors for silver.
    """

    def get_captor_faction(self, *, warrior: Warrior) -> Faction:
        current_savegame: Savegame = get_current_savegame_for_request(request=self.request)
        if current_savegame is None or current_savegame.player_faction_id is None:
            raise Http404

        return get_object_or_404(
            Faction.objects.for_player_faction(faction_id=current_savegame.player_faction_id).filter(
                captured_warriors=warrior
            ),
            pk=self.kwargs["faction_id"],
        )


class WarriorRecruitCapturedView(RunningSavegameRequiredMixin, CapturedWarriorActionMixin, generic.DetailView):
    model = Warrior
    http_method_names = ("post",)

    def post(self, request, *args, **kwargs):
        obj = self.get_object()
        faction = self.get_captor_faction(warrior=obj)
        current_savegame: Savegame = get_current_savegame_for_request(request=self.request)

        handle_message(RecruitCapturedWarrior(faction=faction, warrior=obj, month=current_savegame.current_month))

        response = HttpResponse(status=HTTPStatus.OK)
        response["HX-Trigger"] = json.dumps(
            {
                "notification": "Captured warrior joined your ranks",
                "loadFactionWarriorList": "-",
                "loadFactionCapturedWarriorList": "-",
            }
        )

        return response


class WarriorEnslaveCapturedView(RunningSavegameRequiredMixin, CapturedWarriorActionMixin, generic.DetailView):
    model = Warrior
    http_method_names = ("post",)

    def post(self, request, *args, **kwargs):
        obj = self.get_object()
        faction = self.get_captor_faction(warrior=obj)
        current_savegame: Savegame = get_current_savegame_for_request(request=self.request)

        handle_message(EnslaveCapturedWarrior(faction=faction, warrior=obj, month=current_savegame.current_month))

        response = HttpResponse(status=HTTPStatus.OK)
        response["HX-Trigger"] = json.dumps(
            {
                "notification": "Captured warrior was sold into slavery",
                "loadFactionCapturedWarriorList": "-",
            }
        )

        return response
