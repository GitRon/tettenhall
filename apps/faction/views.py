import json

from django.shortcuts import render
from django.views import generic

from apps.core.event_loop.runner import handle_message
from apps.faction.messages.commands.warrior import DraftWarriorFromFyrd
from apps.faction.models.faction import Faction


class FactionDetailView(generic.DetailView):
    model = Faction
    template_name = "faction/faction_detail.html"


class FactionItemListView(generic.DetailView):
    model = Faction
    template_name = "faction/item/components/item_list.html"


class FactionWarriorListView(generic.DetailView):
    model = Faction
    template_name = "faction/warrior/components/warrior_list.html"


class DraftWarriorFromFyrdView(generic.DetailView):
    model = Faction
    http_method_names = ("post",)
    template_name = "faction/warrior/components/fyrd_card.html"

    def post(self, request, *args, **kwargs):
        obj = self.get_object()

        handle_message(DraftWarriorFromFyrd.generator(context_data={"faction": obj}))
        response = render(request, self.template_name, {"faction": obj})

        response["HX-Trigger"] = json.dumps(
            {
                "notification": "New Warrior drafted",
                "loadFactionWarriorList": "-",
            }
        )

        return response
