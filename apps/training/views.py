from django.urls import reverse_lazy
from django.views import generic

from apps.savegame.mixins import PlayerFactionScopedQuerysetMixin, SavegameScopedQuerysetMixin
from apps.savegame.models.savegame import Savegame
from apps.training.forms import TrainingForm
from apps.training.models.training import Training


class TrainingListView(SavegameScopedQuerysetMixin, generic.ListView):
    model = Training
    template_name = "training/training_list.html"

    def get_context_data(self, *, object_list=None, **kwargs):
        context = super().get_context_data(object_list=object_list, **kwargs)

        # A user without an active savegame has neither, and dereferencing it answered the page
        # with a server error
        current_savegame: Savegame = Savegame.objects.get_current_savegame(user_id=self.request.user.id)
        context["faction"] = current_savegame.player_faction if current_savegame else None
        # Every faction of the savegame owns a training row, so this has to name the player's own
        context["current_training"] = (
            Training.objects.for_player_faction(faction_id=current_savegame.player_faction_id).first()
            if current_savegame and current_savegame.player_faction_id
            else None
        )
        return context


class TrainingEditView(PlayerFactionScopedQuerysetMixin, generic.UpdateView):
    # Editing a rival's training row changes what its warriors improve each month, so the savegame
    # is the wrong scope here
    model = Training
    form_class = TrainingForm
    template_name = "training/training_edit.html"
    success_url = reverse_lazy("training:training-list-view")
