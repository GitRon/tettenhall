import json
from http import HTTPStatus

from django.db.models import QuerySet
from django.http import HttpResponse
from django.views import generic
from django.views.generic.detail import SingleObjectMixin
from queuebie.runner import handle_message

from apps.warband.finance.models import Transaction
from apps.warband.item.forms.item import AssignItemForm
from apps.warband.item.messages.commands.item import BuyItem, EquipItem, SellItem
from apps.warband.item.models.item import Item
from apps.warband.item.services.handout import get_handout_note
from apps.warband.savegame.mixins import (
    PlayerFactionScopedQuerysetMixin,
    RunningSavegameRequiredMixin,
    SavegameScopedQuerysetMixin,
)
from apps.warband.savegame.models.savegame import Savegame
from apps.warband.savegame.services.current_savegame import get_current_savegame_for_request


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


class ItemAssignView(RunningSavegameRequiredMixin, PlayerFactionScopedQuerysetMixin, SingleObjectMixin, generic.View):
    """
    Hands a piece of the player's gear to one of his men, from the faction page.

    The other way in is the slot on the warrior's own page, which starts from the man and asks which
    item. This starts from the item and asks which man - the way the player is already thinking when
    something new arrives - and it is what keeps a new sword from having to be walked down the roster
    a page at a time.

    Scoped to the player faction, not the savegame: a rival's gear is in the savegame too, and the id
    from the URL would otherwise be enough to re-arm a rival's war band. Which slot the item fills is
    the item's own business rather than a URL segment, so there is no free parameter to validate.
    """

    model = Item
    http_method_names = ("post",)

    def post(self, request, *args, **kwargs) -> HttpResponse:
        obj = self.get_object()
        form = AssignItemForm(request.POST, item=obj)

        if not form.is_valid():
            response = HttpResponse(status=HTTPStatus.NO_CONTENT)
            response["HX-Trigger"] = json.dumps({"notification": "That warrior is not on your roster."})
            return response

        warrior = form.cleaned_data["warrior"]
        slot = obj.gear_slot
        # Read before the handler moves anything: the sentence is about the state the move changes,
        # and afterwards there is nothing left to read it off. The event carries the facts and this
        # view words its own line from them - see docs/patterns/message-bus.md.
        note = get_handout_note(warrior=warrior, item=obj, slot=slot)

        handle_message(EquipItem(warrior=warrior, item=obj, slot=slot))

        triggers = {"loadFactionItemList": "-", "loadFactionWarriorList": "-"}
        if note:
            triggers["notification"] = note

        response = HttpResponse(status=HTTPStatus.OK)
        response["HX-Trigger"] = json.dumps(triggers)
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
