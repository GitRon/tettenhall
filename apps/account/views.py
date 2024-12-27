from django.views import generic

from apps.faction.models.faction import Faction
from apps.week.models.player_week_log import PlayerWeekLog


class DashboardView(generic.TemplateView):
    template_name = "account/dashboard.html"

    def get_context_data(self, **kwargs):
        context = super().get_context_data(**kwargs)

        # TODO: query for current savegame
        context["player_week_logs"] = PlayerWeekLog.objects.all()
        # TODO: get from current savegame
        context["faction"] = Faction.objects.get(id=2)
        return context
