from django.db.models import QuerySet
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
