import json

from django.http import HttpResponse
from django.shortcuts import get_object_or_404, render
from django.views import generic

from apps.core.event_loop.runner import handle_message
from apps.faction.models.faction import Faction
from apps.skirmish.models.warrior import Warrior
from apps.warrior.forms.warrior import WarriorForm
from apps.warrior.messages.commands.warrior import EnslaveCapturedWarrior, RecruitCapturedWarrior


class WarriorDetailView(generic.DetailView):
    model = Warrior
    template_name = "warrior/warrior_detail.html"


class WarriorWeaponUpdateView(generic.UpdateView):
    model = Warrior
    form_class = WarriorForm
    template_name = "warrior/components/warrior_field_edit.html"
    object = None
    htmx_field = None

    def get_form_kwargs(self):
        kwargs = super().get_form_kwargs()
        self.htmx_field = self.kwargs.get("htmx_attribute", None)
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


class WarriorRecruitCapturedView(generic.DetailView):
    model = Warrior
    http_method_names = ("post",)

    def post(self, request, *args, **kwargs):
        obj = self.get_object()
        faction = get_object_or_404(Faction, pk=kwargs["faction_id"])

        handle_message(RecruitCapturedWarrior(RecruitCapturedWarrior.Context(faction=faction, warrior=obj)))

        response = HttpResponse(status=200)
        response["HX-Trigger"] = json.dumps(
            {
                "notification": "Captured warrior joined your ranks",
                "loadFactionWarriorList": "-",
                "loadFactionCapturedWarriorList": "-",
            }
        )

        return response


class WarriorEnslaveCapturedView(generic.DetailView):
    model = Warrior
    http_method_names = ("post",)

    def post(self, request, *args, **kwargs):
        obj = self.get_object()
        faction = get_object_or_404(Faction, pk=kwargs["faction_id"])

        handle_message(EnslaveCapturedWarrior(EnslaveCapturedWarrior.Context(faction=faction, warrior=obj)))

        response = HttpResponse(status=200)
        response["HX-Trigger"] = json.dumps(
            {
                "notification": "Captured warrior was sold into slavery",
                "loadFactionCapturedWarriorList": "-",
            }
        )

        return response
