import json

from django.contrib import messages
from django.db.models import QuerySet
from django.shortcuts import render
from django.urls import reverse
from django.views import generic
from django.views.generic.detail import SingleObjectMixin
from queuebie.runner import handle_message

from apps.faction.forms.faction_attack import FactionAttackForm
from apps.faction.messages.commands.warrior import DraftWarriorFromFyrd
from apps.faction.models.faction import Faction
from apps.savegame.mixins import (
    PlayerFactionScopedQuerysetMixin,
    RunningSavegameRequiredMixin,
    SavegameScopedQuerysetMixin,
)
from apps.savegame.models.savegame import Savegame
from apps.skirmish.messages.commands.skirmish import AttackFaction
from apps.skirmish.models.warrior import Warrior


class FactionDetailView(SavegameScopedQuerysetMixin, generic.DetailView):
    model = Faction
    template_name = "faction/faction_detail.html"

    def get_context_data(self, **kwargs):
        context = super().get_context_data(**kwargs)
        context["warrior_list"] = Warrior.objects.exclude_dead().filter_faction(faction_id=self.object.id)

        # Asked through the same queryset the attack view resolves its target with, so the button
        # and the page it leads to can never disagree about who may be attacked
        current_savegame: Savegame = Savegame.objects.get_current_savegame(user_id=self.request.user.id)
        # This template serves the player's own faction and a rival's alike, so it has to know which
        # it is looking at: "My faction" over a rival's details is simply wrong, and the fyrd card
        # offers a draft the scoping on DraftWarriorFromFyrdView can only refuse.
        # A savegame without a player faction gives None here, which no faction id equals - so it
        # renders as a rival's page, which is right: there is no own faction yet.
        context["is_player_faction"] = self.object.id == current_savegame.player_faction_id
        context["can_be_attacked"] = (
            Faction.objects.attackable_by(
                player_faction=current_savegame.player_faction, month=current_savegame.current_month
            )
            .filter(id=self.object.id)
            .exists()
        )
        # A button that simply vanishes teaches the player nothing, and "every warrior fights once a
        # month" is the rule he is most likely to walk into without noticing. Only said where marching
        # is what is actually missing though: this faction has to be one he could otherwise march on,
        # or the sentence is a non sequitur on his own faction and on one already knocked out.
        player_faction = current_savegame.player_faction
        context["has_marched_this_month"] = (
            not context["can_be_attacked"]
            and player_faction is not None
            and Faction.objects.attackable_targets(player_faction=player_faction).filter(id=self.object.id).exists()
            and player_faction.has_marched_this_month(month=current_savegame.current_month)
        )

        return context


class FactionItemListView(SavegameScopedQuerysetMixin, generic.DetailView):
    model = Faction
    template_name = "faction/item/components/item_list.html"


class FactionWarriorListView(SavegameScopedQuerysetMixin, generic.DetailView):
    model = Faction
    template_name = "faction/warrior/components/warrior_list.html"

    def get_context_data(self, **kwargs):
        context = super().get_context_data(**kwargs)
        context["warrior_list"] = Warrior.objects.exclude_dead().filter_faction(faction_id=self.object.id)
        return context


class FactionCapturedWarriorListView(SavegameScopedQuerysetMixin, generic.DetailView):
    model = Faction
    template_name = "faction/warrior/components/captured_warrior_list.html"


class DraftWarriorFromFyrdView(RunningSavegameRequiredMixin, PlayerFactionScopedQuerysetMixin, generic.DetailView):
    # Drafting is a write on the faction from the URL, so being in the current savegame is not
    # enough - that would draft into a rival faction and spend its fyrd reserve
    model = Faction
    http_method_names = ("post",)
    template_name = "faction/warrior/components/fyrd_card.html"

    def post(self, request, *args, **kwargs):
        obj = self.get_object()
        current_savegame: Savegame = Savegame.objects.get_current_savegame(user_id=self.request.user.id)

        handle_message(DraftWarriorFromFyrd(faction=obj, month=current_savegame.current_month))
        response = render(request, self.template_name, {"faction": obj})

        response["HX-Trigger"] = json.dumps(
            {
                "notification": "New Warrior drafted",
                "loadFactionWarriorList": "-",
                "loadFactionItemList": "-",
            }
        )

        return response


class AttackTargetMixin:
    """
    Resolves the rival the player is marching against.

    A separate mixin purely for the ordering. A "dispatch" written on the view itself runs before
    every mixin the view inherits, so resolving the target there answered a decided savegame with a
    404 about a rival it could no longer offer - the game being over never got a word in.
    Sitting behind RunningSavegameRequiredMixin in the bases puts that guard first, which is the
    difference between "not found" and a page telling the player why.
    """

    object = None
    current_savegame: Savegame = None

    def dispatch(self, request, *args, **kwargs):
        self.current_savegame = Savegame.objects.get_current_savegame(user_id=request.user.id)
        self.object = self.get_object()
        return super().dispatch(request, *args, **kwargs)


class FactionAttackView(RunningSavegameRequiredMixin, AttackTargetMixin, SingleObjectMixin, generic.FormView):
    """
    Marches the player's war band against a rival faction.

    Carries no scoping mixin: every rule about who may be attacked - the savegame among them - lives
    in "attackable_by()", and layering a second, looser scope on top would only invite the two to
    disagree.
    """

    model = Faction
    form_class = FactionAttackForm
    template_name = "faction/faction_attack.html"

    def get_queryset(self) -> QuerySet:
        if self.current_savegame is None:
            return super().get_queryset().none()

        return (
            super()
            .get_queryset()
            .attackable_by(
                player_faction=self.current_savegame.player_faction,
                month=self.current_savegame.current_month,
            )
        )

    def get_form_kwargs(self):
        kwargs = super().get_form_kwargs()
        # Resolving the target above already proved there is one, so this cannot come back empty
        kwargs["leader"] = self.current_savegame.player_faction.get_available_leader(
            month=self.current_savegame.current_month
        )
        kwargs["month"] = self.current_savegame.current_month
        return kwargs

    def get_context_data(self, **kwargs):
        context = super().get_context_data(**kwargs)
        context["object"] = self.object
        return context

    def form_valid(self, form):
        response = super().form_valid(form)

        handle_message(
            AttackFaction(
                attacking_faction=self.current_savegame.player_faction,
                # The scoped object from the URL, not a posted field: which rival is attacked is
                # decided by the route that was allowed to be reached
                target_faction=self.object,
                assigned_warriors=form.get_assigned_warriors(),
                month=self.current_savegame.current_month,
            )
        )

        # A message rather than an "HX-Trigger": this form is a plain post and the response is a
        # redirect, so the browser navigates away and nothing is left to read a header. The same
        # toast comes out the other end, because base.html renders "messages" on every page.
        messages.add_message(self.request, messages.SUCCESS, f"Your war band marches on {self.object}.")

        return response

    def get_success_url(self):
        return reverse("skirmish:skirmish-list-view")


class MonthlyCostOverview(SavegameScopedQuerysetMixin, generic.DetailView):
    model = Faction
    template_name = "faction/faction/components/current_cost_card.html"

    def get_context_data(self, **kwargs):
        context = super().get_context_data(**kwargs)
        # Fetch current savegame record
        current_savegame: Savegame = Savegame.objects.get_current_savegame(user_id=self.request.user.id)

        # The wage bill itself is not assembled here. It comes off "wage_bill_payroll", the same
        # projection the salary run bills from and the navbar warns from, which the finance context
        # processor puts on every render - computing it here again is what made the card and the
        # month disagree about who goes unpaid. Only the income is this card's own, because it is
        # the one number on it that nothing else shows - and it is read off the town, the same way
        # the month reads it, rather than assembled from a building here.
        context["building_income_amount"] = current_savegame.player_faction.town.get_monthly_income()

        return context


class TownSquareView(SavegameScopedQuerysetMixin, generic.DetailView):
    model = Faction
    template_name = "faction/town_square.html"


class FactionShopItemListView(SavegameScopedQuerysetMixin, generic.DetailView):
    model = Faction
    template_name = "faction/item/components/shop_item_list.html"

    def get_context_data(self, **kwargs):
        context = super().get_context_data(**kwargs)
        context["item_list"] = self.object.available_items.all()
        return context
