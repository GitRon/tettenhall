from django.http import HttpResponse
from django.urls import reverse
from django.views import generic

from apps.core.event_loop.runner import handle_message
from apps.marketplace.messages.commands.item import RestockMarketplaceItems
from apps.marketplace.messages.commands.warrior import RestockPubMercenaries
from apps.marketplace.models.marketplace import Marketplace


class FinishWeekView(generic.View):
    http_method_names = ("post",)

    def post(self, request, *args, **kwargs):
        # todo increment current week/year in savegame

        # todo what needs to happen:
        #  - refresh player warrior morale
        #  - start quests / skirmishes?
        #  - heal warriors
        #  - refresh market item and warriors
        #  - notifications for the dashboard / player
        marketplace = Marketplace.objects.all().first()
        handle_message(
            [
                # todo take week from savegame
                RestockMarketplaceItems.generator(context_data={"marketplace": marketplace, "week": 1}),
                RestockPubMercenaries.generator(context_data={"marketplace": marketplace, "week": 1}),
            ]
        )

        response = HttpResponse(status=200)
        response["HX-Redirect"] = reverse("account:dashboard-view")
        return response
