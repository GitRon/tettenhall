from django.contrib import messages
from django.urls import reverse
from django.views import generic
from django.views.generic.detail import SingleObjectMixin
from queuebie.runner import handle_message

from apps.warband.quest.forms.quest_accept import QuestAcceptForm
from apps.warband.quest.messages.commands.quest import AcceptQuest
from apps.warband.quest.models.quest import Quest
from apps.warband.quest.quests import QUESTS_BY_NAME
from apps.warband.savegame.mixins import PlayerFactionScopedQuerysetMixin, RunningSavegameRequiredMixin
from apps.warband.savegame.models.savegame import Savegame
from apps.warband.savegame.services.current_savegame import get_current_savegame_for_request


class QuestLookupMixin:
    """
    Resolves the offer the player is answering.

    A separate mixin purely for the ordering, the way "AttackTargetMixin" is. A "dispatch" written on
    the view itself runs before every mixin the view inherits, so a decided savegame would get a 404
    about an offer it no longer has instead of the notice that the game is over. Sitting behind
    RunningSavegameRequiredMixin in the bases puts that guard first.
    """

    object = None
    current_savegame: Savegame = None

    def dispatch(self, request, *args, **kwargs):
        # The savegame first: resolving the quest runs the scoped queryset, which needs the month
        self.current_savegame = get_current_savegame_for_request(request=request)
        self.object = self.get_object()
        return super().dispatch(request, *args, **kwargs)


class QuestAcceptView(
    RunningSavegameRequiredMixin,
    QuestLookupMixin,
    PlayerFactionScopedQuerysetMixin,
    SingleObjectMixin,
    generic.FormView,
):
    model = Quest
    form_class = QuestAcceptForm
    template_name = "quest/quest_detail.html"

    def get_queryset(self):
        # A logged-in user need not have a savegame yet, and there is no month to ask about then. The
        # scoping mixin would narrow to nothing anyway, so this only has to avoid dereferencing it.
        if self.current_savegame is None:
            return super().get_queryset().none()

        # Only this month's offers. The board is redrawn when the month turns, and a stale tab must
        # not send men on an errand that was never offered for the month they would be away in
        return super().get_queryset().offered_in(month=self.current_savegame.current_month)

    def get_form_kwargs(self):
        kwargs = super().get_form_kwargs()
        kwargs["quest"] = self.object
        kwargs["month"] = self.current_savegame.current_month
        return kwargs

    def get_context_data(self, **kwargs):
        context = super().get_context_data(**kwargs)
        context["object"] = self.object
        context["entry"] = QUESTS_BY_NAME[self.object.quest]
        return context

    def form_valid(self, form):
        response = super().form_valid(form)

        handle_message(
            AcceptQuest(
                accepting_faction=self.current_savegame.player_faction,
                # The scoped object from the URL: nothing posted names the quest
                quest=self.object,
                # The form cleans to a queryset, and messages carry lists
                assigned_warriors=list(form.cleaned_data["assigned_warriors"]),
                month=self.current_savegame.current_month,
            )
        )

        # A message rather than an "HX-Trigger": this form is a plain post and the response is a
        # redirect, so the browser navigates away and nothing is left to read a header
        messages.add_message(self.request, messages.SUCCESS, f"Your men set out: {self.object}")

        return response

    def get_success_url(self):
        # Back to the board, which now names who is away and what is still on offer
        return reverse("warband:town-board-view")
