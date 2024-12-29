import json

from django.urls import reverse
from django.views import generic
from django.views.generic.detail import SingleObjectMixin

from apps.core.event_loop.runner import handle_message
from apps.quest.forms.quest_accept import QuestAcceptForm
from apps.quest.messages.commands.quest import AcceptQuest
from apps.quest.models.quest import Quest
from apps.savegame.models.savegame import Savegame


class QuestAcceptView(SingleObjectMixin, generic.FormView):
    model = Quest
    form_class = QuestAcceptForm
    template_name = "quest/quest_detail.html"
    object = None
    current_savegame: Savegame = None

    def dispatch(self, request, *args, **kwargs):
        self.object = self.get_object()
        self.current_savegame = Savegame.objects.get_current_savegame(user_id=self.request.user.id)
        return super().dispatch(request, *args, **kwargs)

    def get_form_kwargs(self):
        kwargs = super().get_form_kwargs()
        kwargs["quest_id"] = self.object.id
        kwargs["player_faction_id"] = self.current_savegame.player_faction_id
        return kwargs

    def get_context_data(self, **kwargs):
        context = super().get_context_data(**kwargs)
        context["object"] = self.object
        return context

    def form_valid(self, form):
        response = super().form_valid(form)

        handle_message(
            AcceptQuest(
                AcceptQuest.Context(
                    accepting_faction=self.current_savegame.player_faction,
                    quest=form.cleaned_data["quest"],
                    assigned_warriors=form.cleaned_data["assigned_warriors"],
                )
            )
        )

        response["HX-Trigger"] = json.dumps(
            {
                "loadFactionItemList": "-",
                "loadFactionWarriorList": "-",
            }
        )
        return response

    def get_success_url(self):
        return reverse("marketplace:marketplace-view", args=(self.current_savegame.marketplace_id,))
