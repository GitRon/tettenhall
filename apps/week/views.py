import json

from django.http import HttpResponse
from django.urls import reverse
from django.views import generic

from apps.core.event_loop.runner import handle_message
from apps.faction.messages.commands.faction import (
    DetermineInjuredWarriors,
    DetermineWarriorsWithLowMorale,
    PayWeeklyWarriorSalaries,
    ReplenishFyrdReserve,
)
from apps.faction.models.faction import Faction
from apps.marketplace.messages.commands.item import RestockMarketplaceItems
from apps.marketplace.messages.commands.quest import OfferNewQuestsOnBoard
from apps.marketplace.messages.commands.warrior import RestockPubMercenaries
from apps.marketplace.models.marketplace import Marketplace
from apps.training.messages.commands.training import TrainWarriors
from apps.training.models.training import Training
from apps.week.models.player_week_log import PlayerWeekLog


class FinishWeekView(generic.View):
    http_method_names = ("post",)

    def post(self, request, *args, **kwargs):
        # todo increment current week/year in savegame

        # todo what needs to happen:
        #  - start quests / skirmishes?
        marketplace = Marketplace.objects.all().first()
        # todo take faction from savegame
        faction = Faction.objects.get(id=2)
        handle_message(
            [
                # todo take week from save game
                # todo brauch ich hier unbedingt die woche? ich könnte ja einfach am ende der runde alle alten schließen
                RestockMarketplaceItems(RestockMarketplaceItems.Context(marketplace=marketplace, week=1)),
                RestockPubMercenaries(RestockPubMercenaries.Context(marketplace=marketplace, week=1)),
                OfferNewQuestsOnBoard(OfferNewQuestsOnBoard.Context(marketplace=marketplace, week=1)),
                ReplenishFyrdReserve(ReplenishFyrdReserve.Context(faction=faction, week=1)),
                PayWeeklyWarriorSalaries(PayWeeklyWarriorSalaries.Context(faction=faction, week=1)),
                DetermineWarriorsWithLowMorale(DetermineWarriorsWithLowMorale.Context(faction=faction, week=1)),
                DetermineInjuredWarriors(DetermineInjuredWarriors.Context(faction=faction, week=1)),
                # todo have a proper training QS (not here as well)
                TrainWarriors(TrainWarriors.Context(faction=faction, training=Training.objects.all().first(), week=1)),
            ]
        )

        response = HttpResponse(status=200)
        response["HX-Redirect"] = reverse("account:dashboard-view")
        return response


class PlayerWeekLogListView(generic.ListView):
    model = PlayerWeekLog
    template_name = "player-week-log/components/player_week_log_list.html"

    def get_queryset(self):
        # todo we have to filter for the save game/faction
        return super().get_queryset()

    def get_context_data(self, *, object_list=None, **kwargs):
        context = super().get_context_data(object_list=object_list, **kwargs)
        context["faction"] = Faction.objects.get(id=2)
        return context


class AcknowledgePlayerWeekLogView(generic.DeleteView):
    model = PlayerWeekLog
    http_method_names = ("delete",)

    def delete(self, request, *args, **kwargs):
        # todo add some validation when we have save games

        super().delete(request, *args, **kwargs)

        response = HttpResponse(status=202)
        response["HX-Trigger"] = json.dumps(
            {
                "loadMessageList": "-",
            }
        )
        return response

    def get_success_url(self):
        return None
