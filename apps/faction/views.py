import json

from django.db.models import QuerySet, Sum
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
        context["can_be_attacked"] = (
            Faction.objects.attackable_by(
                player_faction=current_savegame.player_faction, month=current_savegame.current_month
            )
            .filter(id=self.object.id)
            .exists()
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


class FactionAttackView(RunningSavegameRequiredMixin, SingleObjectMixin, generic.FormView):
    """
    Marches the player's war band against a rival faction.

    Carries no scoping mixin: every rule about who may be attacked - the savegame among them - lives
    in "attackable_by()", and layering a second, looser scope on top would only invite the two to
    disagree. A decided savegame never gets past it either, since it has neither a leader left to
    march nor a rival still standing, but the guard is carried all the same because a view
    dispatching a command is not the place to reason about that.
    """

    model = Faction
    form_class = FactionAttackForm
    template_name = "faction/faction_attack.html"
    object = None
    current_savegame: Savegame = None

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

    def dispatch(self, request, *args, **kwargs):
        self.current_savegame = Savegame.objects.get_current_savegame(user_id=self.request.user.id)
        self.object = self.get_object()
        return super().dispatch(request, *args, **kwargs)

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

        response["HX-Trigger"] = json.dumps(
            {
                "notification": f"Your war band marches on {self.object}",
                "loadFactionWarriorList": "-",
            }
        )
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

        player_faction = current_savegame.player_faction
        # TODO: put in manager
        context["monthly_salary_amount"] = (
            player_faction.warriors.exclude(condition=Warrior.ConditionChoices.CONDITION_DEAD).aggregate(
                sum_monthly_salary=Sum("monthly_salary")
            )["sum_monthly_salary"]
            or 0
        )
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
