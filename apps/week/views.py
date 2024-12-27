import json

from django.db.models import QuerySet
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
from apps.savegame.mixins import CurrentSavegameMixin
from apps.savegame.models.savegame import Savegame
from apps.training.messages.commands.training import TrainWarriors
from apps.training.models.training import Training
from apps.week.models.player_week_log import PlayerWeekLog


class FinishWeekView(CurrentSavegameMixin, generic.View):
    http_method_names = ("post",)

    def post(self, request, *args, **kwargs) -> HttpResponse:
        # Fetch current savegame record
        context_data = self.get_context_data()
        current_savegame: Savegame = context_data["current_savegame"]

        # Increment current week
        current_week = current_savegame.current_week + 1
        current_savegame.current_week = current_week
        current_savegame.save()

        # Get placer faction
        faction = current_savegame.player_faction

        marketplace = Marketplace.objects.all().first()
        handle_message(
            [
                # TODO: maybe close all previous messages? do we want to keep them?
                RestockMarketplaceItems(RestockMarketplaceItems.Context(marketplace=marketplace, week=current_week)),
                RestockPubMercenaries(RestockPubMercenaries.Context(marketplace=marketplace, week=current_week)),
                OfferNewQuestsOnBoard(OfferNewQuestsOnBoard.Context(marketplace=marketplace, week=current_week)),
                ReplenishFyrdReserve(ReplenishFyrdReserve.Context(faction=faction, week=current_week)),
                PayWeeklyWarriorSalaries(PayWeeklyWarriorSalaries.Context(faction=faction, week=current_week)),
                DetermineWarriorsWithLowMorale(
                    DetermineWarriorsWithLowMorale.Context(faction=faction, week=current_week)
                ),
                DetermineInjuredWarriors(DetermineInjuredWarriors.Context(faction=faction, week=current_week)),
                # TODO: have a proper training QS (not here as well)
                TrainWarriors(
                    TrainWarriors.Context(faction=faction, training=Training.objects.all().first(), week=current_week)
                ),
            ]
        )

        response = HttpResponse(status=200)
        response["HX-Redirect"] = reverse("account:dashboard-view")
        return response


class PlayerWeekLogListView(generic.ListView):
    model = PlayerWeekLog
    template_name = "player-week-log/components/player_week_log_list.html"

    def get_queryset(self) -> QuerySet:
        # TODO: we have to filter for the save game/faction
        return super().get_queryset()

    def get_context_data(self, *, object_list=None, **kwargs) -> dict:
        context = super().get_context_data(object_list=object_list, **kwargs)
        context["faction"] = Faction.objects.get(id=2)
        return context


class AcknowledgePlayerWeekLogView(generic.DeleteView):
    model = PlayerWeekLog
    http_method_names = ("delete",)

    def delete(self, request, *args, **kwargs) -> HttpResponse:
        # TODO: add some validation when we have save games

        super().delete(request, *args, **kwargs)

        response = HttpResponse(status=202)
        response["HX-Trigger"] = json.dumps(
            {
                "loadMessageList": "-",
            }
        )
        return response

    def get_success_url(self) -> None:
        return None
