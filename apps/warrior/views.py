from django.shortcuts import render
from django.views import generic

from apps.skirmish.models.warrior import Warrior
from apps.warrior.forms.warrior import WarriorForm


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
