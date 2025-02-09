import json
from http import HTTPStatus

from django.http import HttpResponse
from django.views import generic
from django.views.generic.detail import SingleObjectMixin
from queuebie.runner import handle_message

from apps.finance.models import Transaction
from apps.item.messages.commands.item import BuyItem, SellItem
from apps.item.models.item import Item
from apps.savegame.models.savegame import Savegame


class ItemSellView(SingleObjectMixin, generic.View):
    model = Item
    http_method_names = ("post",)

    def post(self, *args, **kwargs):
        obj = self.get_object()

        handle_message(SellItem(selling_faction=obj.owner, item=obj))

        response = HttpResponse(status=HTTPStatus.OK)
        response["HX-Trigger"] = json.dumps(
            {
                "loadFactionItemList": "-",
                "loadFactionWarriorList": "-",
            }
        )
        return response


class ItemBuyView(SingleObjectMixin, generic.View):
    model = Item
    http_method_names = ("post",)

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

        handle_message(BuyItem(price=obj.price, item=obj, buying_faction=current_savegame.player_faction))

        response = HttpResponse(status=HTTPStatus.OK)
        response["HX-Trigger"] = json.dumps(
            {
                "loadMarketplaceItemList": "-",
            }
        )
        return response
