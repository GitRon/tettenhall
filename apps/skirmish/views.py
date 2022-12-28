import json

from django.views import generic

from apps.skirmish.models.battle_log import BattleLog
from apps.skirmish.models.faction import Faction
from apps.skirmish.services.fight import FightService


class SkirmishView(generic.TemplateView):
    template_name = "skirmish/skirmish.html"

    def get_context_data(self, **kwargs):
        context = super().get_context_data(**kwargs)

        context["faction_1"] = Faction.objects.all().first()
        context["faction_2"] = Faction.objects.all().last()
        context["battle_log"] = BattleLog.objects.all()

        # fixme temp
        service = FightService(
            party_1=context["faction_1"].warriors.all(),
            party_2=context["faction_2"].warriors.all(),
        )
        service.process()

        return context

    def get(self, request, *args, **kwargs):
        response = super().get(request, *args, **kwargs)

        response["HX-Trigger"] = json.dumps(
            {
                "battleReportUpdate": "-",
            }
        )
        return response


class BattleLogUpdateHtmxView(generic.ListView):
    model = BattleLog
    template_name = "skirmish/battle_log/htmx/_report_box.html"
