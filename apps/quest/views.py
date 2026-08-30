from django.contrib import messages
from django.urls import reverse
from django.views import generic
from django.views.generic.detail import SingleObjectMixin
from queuebie.runner import handle_message

from apps.quest.forms.quest_accept import QuestAcceptForm
from apps.quest.messages.commands.quest import AcceptQuest
from apps.quest.models.quest import Quest
from apps.savegame.mixins import PlayerFactionScopedQuerysetMixin, RunningSavegameRequiredMixin
from apps.savegame.models.savegame import Savegame
from apps.savegame.services.current_savegame import get_current_savegame_for_request


class QuestAcceptView(
    RunningSavegameRequiredMixin, PlayerFactionScopedQuerysetMixin, SingleObjectMixin, generic.FormView
):
    model = Quest
    form_class = QuestAcceptForm
    template_name = "quest/quest_detail.html"
    object = None
    current_savegame: Savegame = None

    def get_queryset(self):
        # A logged-in user need not have a savegame yet, and there is no month to ask about then. The
        # scoping mixin would narrow to nothing anyway, so this only has to avoid dereferencing it -
        # the same guard FactionAttackView carries, for the same reason.
        if self.current_savegame is None:
            return super().get_queryset().none()

        # The board and this view are scoped the same way, so the "Accept" link and the page it leads
        # to can never disagree about which quests can still be taken on
        return super().get_queryset().resolvable(month=self.current_savegame.current_month)

    def dispatch(self, request, *args, **kwargs):
        # The savegame first: resolving the quest runs the scoped queryset above, which needs the
        # month to ask whether the target can still field a defender
        self.current_savegame = get_current_savegame_for_request(request=self.request)
        self.object = self.get_object()
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
                accepting_faction=self.current_savegame.player_faction,
                # The scoped object from the URL, not the posted field: the latter is a hidden
                # input and naming someone else's quest in it must not accept that quest
                quest=self.object,
                assigned_warriors=form.cleaned_data["assigned_warriors"],
                month=self.current_savegame.current_month,
            )
        )

        # A message rather than an "HX-Trigger": this form is a plain post and the response is a
        # redirect, so the browser navigates away and nothing is left to read a header
        messages.add_message(self.request, messages.SUCCESS, f'You accepted the quest "{self.object}".')

        return response

    def get_success_url(self):
        return reverse("faction:town-square-view", args=(self.current_savegame.player_faction_id,))
