from django.views import generic

from apps.skirmish.models.faction import Faction


class SkirmishView(generic.TemplateView):
    template_name = 'skirmish/skirmish.html'

    def get_context_data(self, **kwargs):
        context = super().get_context_data(**kwargs)

        context['faction_1'] = Faction.objects.all().first()
        context['faction_2'] = Faction.objects.all().last()

        return context
