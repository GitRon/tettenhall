from django.views import generic

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
