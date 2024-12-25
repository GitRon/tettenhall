from django.urls import reverse_lazy
from django.views import generic

from apps.faction.models.faction import Faction
from apps.training.forms import TrainingForm
from apps.training.models.training import Training


class TrainingListView(generic.ListView):
    model = Training
    template_name = "training/training_list.html"

    def get_context_data(self, *, object_list=None, **kwargs):
        context = super().get_context_data(object_list=object_list, **kwargs)
        # TODO: static player faction
        context["faction"] = Faction.objects.get(id=2)

        # TODO: get training properly
        context["current_training"] = Training.objects.all().first()
        return context


class TrainingEditView(generic.UpdateView):
    model = Training
    form_class = TrainingForm
    template_name = "training/training_edit.html"
    success_url = reverse_lazy("training:training-list-view")
