from django.http import HttpResponseRedirect
from django.urls import reverse_lazy
from django.views import generic
from queuebie.runner import handle_message

from apps.warband.savegame.mixins import PlayerFactionScopedQuerysetMixin, RunningSavegameRequiredMixin
from apps.warband.training.forms import TrainingForm
from apps.warband.training.messages.commands.training import ChangeTrainingRegimen
from apps.warband.training.models.training import Training


class TrainingEditView(RunningSavegameRequiredMixin, PlayerFactionScopedQuerysetMixin, generic.UpdateView):
    # Editing a rival's training row changes what its warriors improve each month, so the savegame
    # is the wrong scope here
    model = Training
    form_class = TrainingForm
    template_name = "training/training_edit.html"
    # Back to where the choice is made and shown. Training is one faction-wide row a new savegame
    # already arrives with a value for, so it is a line on the month's page rather than a place of
    # its own - see docs/patterns/navigation.md.
    success_url = reverse_lazy("warband:dashboard-view")

    def form_valid(self, form):
        # Through the bus rather than the ModelForm's own save, like every other change to the world
        handle_message(ChangeTrainingRegimen(training=self.object, category=form.cleaned_data["category"]))

        return HttpResponseRedirect(self.get_success_url())
