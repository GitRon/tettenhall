from http import HTTPStatus

from django.http import HttpResponse
from django.urls import reverse, reverse_lazy
from django.views import generic
from queuebie.runner import handle_message

from apps.savegame.forms.create_savegame import SavegameCreateForm
from apps.savegame.messages.commands.savegame import CreateNewSavegame
from apps.savegame.mixins import CurrentSavegameMixin
from apps.savegame.models.savegame import Savegame


class SavegameListView(CurrentSavegameMixin, generic.ListView):
    model = Savegame
    template_name = "savegame/savegame_list.html"

    def get_queryset(self):
        return Savegame.objects.for_user(user_id=self.request.user.id)


class SavegameCreateView(CurrentSavegameMixin, generic.FormView):
    model = Savegame
    form_class = SavegameCreateForm
    template_name = "savegame/savegame_create.html"
    success_url = reverse_lazy("account:dashboard-view")

    def form_valid(self, form):
        response = super().form_valid(form)

        # Prepare month
        handle_message(
            CreateNewSavegame(
                town_name=form.cleaned_data["town_name"],
                faction_name=form.cleaned_data["faction_name"],
                faction_culture_id=form.cleaned_data["faction_culture"].id,
                created_by_id=self.request.user.id,
            ),
        )

        return response


class SavegameLoadView(generic.DetailView):
    model = Savegame
    http_method_names = ("post",)

    def get_queryset(self):
        return super().get_queryset().for_user(user_id=self.request.user.id)

    def post(self, request, *args, **kwargs):
        savegame = self.get_object()

        Savegame.objects.activate_savegame(savegame=savegame)

        response = HttpResponse(status=HTTPStatus.OK)
        response["HX-Redirect"] = reverse("account:dashboard-view")
        return response
