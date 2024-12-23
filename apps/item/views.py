import json

from django.http import HttpResponse
from django.views import generic
from django.views.generic.detail import SingleObjectMixin

from apps.core.event_loop.runner import handle_message
from apps.item.messages.commands.item import SellItem
from apps.item.models.item import Item


class ItemSellView(SingleObjectMixin, generic.View):
    model = Item
    http_method_names = ("post",)

    def post(self, *args, **kwargs):
        obj = self.get_object()

        handle_message(SellItem(SellItem.Context(selling_faction=obj.owner, item=obj)))

        response = HttpResponse(status=200)
        response["HX-Trigger"] = json.dumps(
            {
                "loadFactionItemList": "-",
                "loadFactionWarriorList": "-",
            }
        )
        return response
