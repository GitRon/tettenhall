from django.views import generic

from apps.faction.models.faction import Faction
from apps.week.models.player_week_log import PlayerWeekLog


class DashboardView(generic.TemplateView):
    template_name = "account/dashboard.html"

    def get_context_data(self, **kwargs):
        context = super().get_context_data(**kwargs)
        context["player_week_logs"] = PlayerWeekLog.objects.all()
        context["faction"] = Faction.objects.get(id=2)
        return context
