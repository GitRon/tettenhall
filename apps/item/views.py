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
from apps.savegame.mixins import SavegameScopedQuerysetMixin
from apps.savegame.models.savegame import Savegame


class ItemSellView(SavegameScopedQuerysetMixin, SingleObjectMixin, generic.View):
    model = Item
    http_method_names = ("post",)

    def get_queryset(self) -> QuerySet:
        # Only the player's own items can be sold. Being in the right savegame is not enough: the
        # shop and the rival factions have items in it too, and selling those would pay them.
        current_savegame: Savegame = Savegame.objects.get_current_savegame(user_id=self.request.user.id)

        return super().get_queryset().filter(owner=current_savegame.player_faction if current_savegame else None)

    def post(self, *args, **kwargs):
        obj = self.get_object()
        current_savegame: Savegame = Savegame.objects.get_current_savegame(user_id=self.request.user.id)

        handle_message(SellItem(selling_faction=obj.owner, item=obj, month=current_savegame.current_month))

        response = HttpResponse(status=HTTPStatus.OK)
        response["HX-Trigger"] = json.dumps(
            {
                "loadFactionItemList": "-",
                "loadFactionWarriorList": "-",
            }
        )
        return response


class ItemBuyView(SavegameScopedQuerysetMixin, SingleObjectMixin, generic.View):
    model = Item
    http_method_names = ("post",)

    def get_queryset(self) -> QuerySet:
        # Only items on sale, meaning unowned ones. Otherwise any item id of the savegame would do,
        # including the equipment of a rival faction.
        return super().get_queryset().filter(owner__isnull=True)

    def post(self, *args, **kwargs):
        obj = self.get_object()
        current_savegame: Savegame = Savegame.objects.get_current_savegame(user_id=self.request.user.id)

        current_balance = Transaction.objects.current_balance(savegame_id=current_savegame.id)
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
            }
        )
        return response
