import json
from http import HTTPStatus

from django.http import Http404, HttpResponse
from django.shortcuts import get_object_or_404, render
from django.views import generic
from queuebie.runner import handle_message

from apps.faction.models.faction import Faction
from apps.savegame.mixins import RunningSavegameRequiredMixin, SavegameScopedQuerysetMixin
from apps.savegame.models.savegame import Savegame
from apps.skirmish.models.warrior import Warrior
from apps.warrior.forms.warrior import WarriorForm
from apps.warrior.messages.commands.warrior import EnslaveCapturedWarrior, RecruitCapturedWarrior


class WarriorDetailView(SavegameScopedQuerysetMixin, generic.DetailView):
    model = Warrior
    template_name = "warrior/warrior_detail.html"


class WarriorWeaponUpdateView(SavegameScopedQuerysetMixin, generic.UpdateView):
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
    Resolves the faction holding a captured warrior.

    Both facts have to be verified: the faction id arrives in the URL, so it could point at another
    player's faction, and "remove_captive()" is a silent no-op for a warrior that was never
    captured - without the check, a player could enslave his own warriors for silver.
    """

    def get_captor_faction(self, *, warrior: Warrior) -> Faction:
        current_savegame: Savegame = Savegame.objects.get_current_savegame(user_id=self.request.user.id)

        return get_object_or_404(
            Faction.objects.for_savegame(savegame_id=current_savegame.id).filter(captured_warriors=warrior),
            pk=self.kwargs["faction_id"],
        )


class WarriorRecruitCapturedView(RunningSavegameRequiredMixin, CapturedWarriorActionMixin, generic.DetailView):
    model = Warrior
    http_method_names = ("post",)

    def post(self, request, *args, **kwargs):
        obj = self.get_object()
        faction = self.get_captor_faction(warrior=obj)
        current_savegame: Savegame = Savegame.objects.get_current_savegame(user_id=self.request.user.id)

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
        current_savegame: Savegame = Savegame.objects.get_current_savegame(user_id=self.request.user.id)

        handle_message(EnslaveCapturedWarrior(faction=faction, warrior=obj, month=current_savegame.current_month))

        response = HttpResponse(status=HTTPStatus.OK)
        response["HX-Trigger"] = json.dumps(
            {
                "notification": "Captured warrior was sold into slavery",
                "loadFactionCapturedWarriorList": "-",
            }
        )

        return response
