from django.urls import reverse_lazy
from django.views import generic

from apps.savegame.models.savegame import Savegame
from apps.training.forms import TrainingForm
from apps.training.models.training import Training


class TrainingListView(generic.ListView):
    model = Training
    template_name = "training/training_list.html"

    def get_context_data(self, *, object_list=None, **kwargs):
        context = super().get_context_data(object_list=object_list, **kwargs)

        current_savegame: Savegame = Savegame.objects.get_current_savegame(user_id=self.request.user.id)
        context["faction"] = current_savegame.player_faction

        context["current_training"] = Training.objects.for_savegame(savegame_id=current_savegame.id).first()
        return context


class TrainingEditView(generic.UpdateView):
    model = Training
    form_class = TrainingForm
    template_name = "training/training_edit.html"
    success_url = reverse_lazy("training:training-list-view")
