import json
from http import HTTPStatus

from django.contrib import messages
from django.db.models import Count, Q, QuerySet
from django.http import HttpResponse
from django.shortcuts import render
from django.urls import reverse
from django.views import generic
from django.views.generic.detail import SingleObjectMixin
from queuebie.runner import handle_message

from apps.faction.forms.faction_attack import FactionAttackForm
from apps.faction.messages.commands.warrior import DraftWarriorFromFyrd, RecruitPubMercenary
from apps.faction.models.faction import Faction
from apps.finance.models import Transaction
from apps.quest.models.quest import Quest
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
        # month" is the rule he is most likely to walk into without noticing. Three separate things can
        # take the button away, so each gets its own sentence: his war band has fought, his leader is
        # unfit to lead one, or the rival's men are spoken for.
        #
        # All three are asked against "rivals_still_standing" rather than "attackable_targets", which is
        # narrower by exactly one of the rules being explained: a faction excluded for having committed
        # defenders would drop out of the test for whether to explain why it is excluded. Anything
        # outside that queryset never offered a fight in the first place - the player's own faction, one
        # already knocked out - and a sentence about it would be a non sequitur.
        player_faction = current_savegame.player_faction
        is_a_standing_rival = (
            player_faction is not None
            and Faction.objects.rivals_still_standing(player_faction=player_faction).filter(id=self.object.id).exists()
        )
        # The leader decides which of the three applies, so he is asked once. Busy is the first, unfit
        # the second, and fit and free means the refusal is the rival's doing - the three are exclusive
        # by construction rather than by the order the template happens to test them in.
        has_available_leader = (
            player_faction is not None
            and player_faction.get_available_leader(month=current_savegame.current_month) is not None
        )
        context["has_marched_this_month"] = (
            not context["can_be_attacked"]
            and is_a_standing_rival
            and player_faction.has_marched_this_month(month=current_savegame.current_month)
        )
        # Not busy and still unavailable means wounded or routed. "Your warriors have already fought" is
        # untrue of him and blaming the rival would be worse, so this is the one that says what the
        # player can actually do about it: mend him.
        context["leader_cannot_march"] = (
            not context["can_be_attacked"]
            and is_a_standing_rival
            and not context["has_marched_this_month"]
            and not has_available_leader
        )
        # Their men are alive and well and already in a fight, which is most often the one the player
        # just had with them, or a quest he accepted against them. Only said once the player could
        # otherwise have marched, or it blames the rival for a refusal that is nothing to do with them.
        context["their_war_band_is_committed"] = (
            not context["can_be_attacked"]
            and is_a_standing_rival
            and has_available_leader
            and not Faction.objects.attackable_targets(
                player_faction=player_faction, month=current_savegame.current_month
            )
            .filter(id=self.object.id)
            .exists()
        )

        return context


class RivalFactionListView(SavegameScopedQuerysetMixin, generic.ListView):
    """
    Everybody the player is playing against, and whether he may march on them.

    The rival's own page already serves a rival as readily as the player's own, so this is the way in
    rather than a second rendering of it: the Attack button lives over there, and until this page
    existed it was reachable only by typing a faction id into the address bar.
    """

    model = Faction
    template_name = "faction/rival_faction_list.html"
    context_object_name = "rival_list"
    current_savegame: Savegame = None

    def setup(self, request, *args, **kwargs) -> None:
        # Resolved once here rather than in both methods below, which each need it: the second call
        # would be a second query for an answer that cannot have changed within one render
        super().setup(request, *args, **kwargs)
        self.current_savegame = Savegame.objects.get_current_savegame(user_id=request.user.id)

    def get_queryset(self) -> QuerySet:
        # Who a rival is, is a question about the player's faction, so without one there is nobody to
        # list - the same "nothing found" the scoping mixins answer with rather than a server error
        if self.current_savegame is None or self.current_savegame.player_faction is None:
            return super().get_queryset().none()

        return (
            super()
            .get_queryset()
            .rivals_in_play(player_faction=self.current_savegame.player_faction)
            # Both are read for every row, so without them the page that exists to answer the
            # per-rival questions in a fixed number of queries would spend two per rival on its own
            # columns. The leader is nullable, so this stays a left join and a leaderless faction
            # still comes back.
            .select_related("culture", "leader")
            # The roster, and deliberately nothing finer: health, morale and gear are knowledge the
            # player has not earned without scouting. Counted in the same query rather than per card,
            # and the dead are left out of it the way the faction page leaves them off the roster.
            .annotate(
                warrior_count=Count("warriors", filter=~Q(warriors__condition=Warrior.ConditionChoices.CONDITION_DEAD))
            )
            .order_by("name")
        )

    def get_context_data(self, **kwargs) -> dict:
        context = super().get_context_data(**kwargs)

        if self.current_savegame is None or self.current_savegame.player_faction is None:
            return context

        player_faction = self.current_savegame.player_faction
        month = self.current_savegame.current_month

        # Both questions are asked once for the whole page and answered out of a set, because asking
        # them per row is a query per row - and it is the same "attackable_by" the attack view
        # resolves its target with, so a button here and the page it leads to cannot disagree.
        attackable_rival_ids = set(
            Faction.objects.attackable_by(
                player_faction=player_faction, month=self.current_savegame.current_month
            ).values_list("id", flat=True)
        )
        # Wider by exactly the "their men are already in a fight" rule, which is what makes it the
        # right guard for the sentences below: outside it a rival never offered a fight in the first
        # place, and explaining a button that was never there would be a non sequitur.
        standing_rival_ids = set(
            Faction.objects.rivals_still_standing(player_faction=self.current_savegame.player_faction).values_list(
                "id", flat=True
            )
        )
        # The leader decides whose refusal it is: unfit or busy and it is the player's own doing, fit
        # and free and the rival's men are the only thing left in the way
        has_available_leader = player_faction.get_available_leader(month=month) is not None

        # Evaluated into a list, because the template iterating the queryset again would re-run it and
        # lose these two answers
        rival_list = list(context[self.context_object_name])
        for rival in rival_list:
            rival.can_be_attacked = rival.id in attackable_rival_ids
            rival.their_war_band_is_committed = (
                has_available_leader and rival.id in standing_rival_ids and rival.id not in attackable_rival_ids
            )
        context[self.context_object_name] = rival_list

        # Said once above the table rather than on every row: both are facts about the player's own
        # war band, so no rival is what decides them, and a row each would be the same sentence
        # repeated as many times as there are rivals. Only said at all while somebody is still
        # standing - over a board that has been cleared it explains the absence of a button that
        # nothing would have offered anyway.
        context["has_marched_this_month"] = (
            len(standing_rival_ids) > 0
            and not has_available_leader
            and player_faction.has_marched_this_month(month=month)
        )
        # Not busy and still unavailable means wounded, routed or dead. Blaming the month would be
        # untrue of him, so this is the one that says what the player can do about it: mend him.
        context["leader_cannot_march"] = (
            len(standing_rival_ids) > 0 and not has_available_leader and not context["has_marched_this_month"]
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


class RecruitPubMercenaryView(
    RunningSavegameRequiredMixin, SavegameScopedQuerysetMixin, SingleObjectMixin, generic.View
):
    """
    Hires the mercenary the player clicked on in his own pub.

    Scoped by pub membership rather than by "PlayerFactionScopedQuerysetMixin": a mercenary nobody has
    hired has no faction at all, so the stricter mixin would narrow every candidate away. The savegame
    scope underneath it is not enough on its own - "Warrior" rows include rival warriors, captives and
    deserters, all of whom would otherwise be hireable by id, and most of them for nothing.

    The URL carries the warrior only. Which pub he is taken from is the player's, read off the
    savegame, because the player hires from his own town - a posted faction could only ever lie about
    that.
    """

    model = Warrior
    http_method_names = ("post",)

    def get_queryset(self) -> QuerySet:
        current_savegame: Savegame = Savegame.objects.get_current_savegame(user_id=self.request.user.id)
        if current_savegame is None or current_savegame.player_faction_id is None:
            return super().get_queryset().none()

        return super().get_queryset().in_pub_of(faction_id=current_savegame.player_faction_id)

    def post(self, *args, **kwargs):
        obj = self.get_object()
        current_savegame: Savegame = Savegame.objects.get_current_savegame(user_id=self.request.user.id)

        current_balance = Transaction.objects.current_balance(faction_id=current_savegame.player_faction_id)
        if current_balance < obj.recruitment_price:
            response = HttpResponse(status=HTTPStatus.NO_CONTENT)
            response["HX-Trigger"] = json.dumps(
                {
                    "notification": "You don't have enough silver to hire this mercenary.",
                }
            )
            return response

        handle_message(
            RecruitPubMercenary(
                warrior=obj,
                faction=current_savegame.player_faction,
                month=current_savegame.current_month,
            )
        )

        # An empty body on purpose: the button swaps its own card out, and the town square has no htmx
        # partial for the pub list to reload in its place.
        response = HttpResponse(status=HTTPStatus.OK)
        response["HX-Trigger"] = json.dumps(
            {
                "notification": f"{obj} joins your war band for {obj.recruitment_price} silver.",
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

    def get_context_data(self, **kwargs):
        context = super().get_context_data(**kwargs)
        # Asked through the same queryset QuestAcceptView resolves its quest with, so a card is only
        # ever shown for a quest that can actually be taken on
        context["quest_list"] = Quest.objects.for_player_faction(faction_id=self.object.id).resolvable(
            month=self.object.savegame.current_month
        )
        return context


class FactionShopItemListView(SavegameScopedQuerysetMixin, generic.DetailView):
    model = Faction
    template_name = "faction/item/components/shop_item_list.html"

    def get_context_data(self, **kwargs):
        context = super().get_context_data(**kwargs)
        context["item_list"] = self.object.available_items.all()
        return context
