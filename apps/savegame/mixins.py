import json
from http import HTTPStatus

from django.db.models import QuerySet
from django.http import HttpResponse
from django.views.generic.base import ContextMixin

from apps.savegame.models.savegame import Savegame


class SavegameScopedQuerysetMixin:
    """
    Restricts a view's queryset to the current savegame.

    Any view resolving an object by primary key needs this, otherwise the id from the URL is enough
    to read or change objects belonging to another player. The model's queryset has to provide
    "for_savegame()".
    """

    def get_queryset(self) -> QuerySet:
        current_savegame = Savegame.objects.get_current_savegame(user_id=self.request.user.id)
        if current_savegame is None:
            return super().get_queryset().none()

        return super().get_queryset().for_savegame(savegame_id=current_savegame.id)


class PlayerFactionScopedQuerysetMixin:
    """
    Restricts a view's queryset to the current savegame's player faction.

    Stricter than SavegameScopedQuerysetMixin and the right choice whenever the view acts on
    something the player owns: a savegame holds the player's faction plus its rivals, so scoping
    to the savegame still lets the id from the URL reach a rival's objects. The model's queryset
    has to provide "for_player_faction()".
    """

    def get_queryset(self) -> QuerySet:
        current_savegame = Savegame.objects.get_current_savegame(user_id=self.request.user.id)
        if current_savegame is None or current_savegame.player_faction_id is None:
            return super().get_queryset().none()

        return super().get_queryset().for_player_faction(faction_id=current_savegame.player_faction_id)


class RunningSavegameRequiredMixin:
    """
    Refuses anything that would change the world once the game has been decided.

    Every view dispatching a command needs this: the outcome is reached the moment a leader falls, and
    a player left holding a finished savegame could otherwise keep drafting, buying and fighting in it.
    Creating or loading a savegame deliberately does not carry it - that is exactly what a player does
    after losing.

    A savegame that is missing entirely is somebody else's problem; the views resolving one already
    answer for that themselves.
    """

    def dispatch(self, request, *args, **kwargs) -> HttpResponse:
        current_savegame = Savegame.objects.get_current_savegame(user_id=request.user.id)

        if current_savegame is not None and current_savegame.outcome != Savegame.OutcomeChoices.OUTCOME_RUNNING:
            response = HttpResponse(status=HTTPStatus.NO_CONTENT)
            response["HX-Trigger"] = json.dumps({"notification": "This game is over. Start a new savegame to play on."})
            return response

        return super().dispatch(request, *args, **kwargs)


class CurrentSavegameMixin(ContextMixin):
    """
    Adds the current savegame to the context.

    Inheriting from ContextMixin keeps "super().get_context_data()" resolvable even on a plain View,
    which is the gotcha this mixin used to guard against with a try/except.
    """

    def get_context_data(self, **kwargs) -> dict:
        context = super().get_context_data(**kwargs)
        context["current_savegame"] = Savegame.objects.get_current_savegame(user_id=self.request.user.id)
        return context
