import json
from http import HTTPStatus

from django.db.models import QuerySet
from django.http import HttpResponse
from django.views import generic
from django.views.generic.detail import SingleObjectMixin
from queuebie.runner import handle_message

from apps.finance.models import Transaction
from apps.item.messages.commands.item import BuyItem, SellItem
from apps.item.models.item import Item
from apps.savegame.mixins import (
    PlayerFactionScopedQuerysetMixin,
    RunningSavegameRequiredMixin,
    SavegameScopedQuerysetMixin,
)
from apps.savegame.models.savegame import Savegame
from apps.savegame.services.current_savegame import get_current_savegame_for_request


class ItemSellView(RunningSavegameRequiredMixin, PlayerFactionScopedQuerysetMixin, SingleObjectMixin, generic.View):
    # Only the player's own items can be sold. Being in the right savegame is not enough: the shop
    # and the rival factions have items in it too, and selling those would pay them.
    model = Item
    http_method_names = ("post",)

    def post(self, *args, **kwargs):
        obj = self.get_object()
        current_savegame: Savegame = get_current_savegame_for_request(request=self.request)

        handle_message(SellItem(selling_faction=obj.owner, item=obj, month=current_savegame.current_month))

        response = HttpResponse(status=HTTPStatus.OK)
        response["HX-Trigger"] = json.dumps(
            {
                "loadFactionItemList": "-",
                "loadFactionWarriorList": "-",
                "updateResourceBar": "-",
            }
        )
        return response


class ItemBuyView(RunningSavegameRequiredMixin, SavegameScopedQuerysetMixin, SingleObjectMixin, generic.View):
    model = Item
    http_method_names = ("post",)

    def get_queryset(self) -> QuerySet:
        # Only what is actually on the player's shop shelf. "Unowned" is not the same thing: the
        # weapons and armor of the pub mercenaries have no owner either, and buying one of those
        # disarms the mercenary standing in the pub.
        current_savegame: Savegame = get_current_savegame_for_request(request=self.request)
        if current_savegame is None or current_savegame.player_faction_id is None:
            return super().get_queryset().none()

        return super().get_queryset().on_sale_at(faction_id=current_savegame.player_faction_id)

    def post(self, *args, **kwargs):
        obj = self.get_object()
        current_savegame: Savegame = get_current_savegame_for_request(request=self.request)

        current_balance = Transaction.objects.current_balance(faction_id=current_savegame.player_faction_id)
        if current_balance < obj.price:
            response = HttpResponse(status=HTTPStatus.NO_CONTENT)
            response["HX-Trigger"] = json.dumps(
                {
                    "notification": "You don't have enough money to buy this item.",
                }
            )
            return response

        handle_message(
            BuyItem(
                price=obj.price,
                item=obj,
                buying_faction=current_savegame.player_faction,
                month=current_savegame.current_month,
            )
        )

        response = HttpResponse(status=HTTPStatus.OK)
        response["HX-Trigger"] = json.dumps(
            {
                "loadShopItemList": "-",
                "updateResourceBar": "-",
            }
        )
        return response
