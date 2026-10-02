import json
from http import HTTPStatus

from django.contrib import messages
from django.db.models import Count, Q, QuerySet
from django.http import Http404, HttpResponse, HttpResponseRedirect
from django.shortcuts import render
from django.urls import reverse
from django.views import generic
from django.views.generic.detail import SingleObjectMixin
from queuebie.runner import handle_message

from apps.warband.faction.forms.faction_attack import FactionAttackForm
from apps.warband.faction.messages.commands.faction import OccupyFaction
from apps.warband.faction.messages.commands.warrior import DraftWarriorFromFyrd, RecruitPubMercenary
from apps.warband.faction.models.faction import Faction
from apps.warband.faction.services.attack_standing import AttackRefusal, get_attack_standing
from apps.warband.faction.services.hiring import get_pub_hire_refusal
from apps.warband.finance.models import Transaction
from apps.warband.item.services.handout import annotate_held_gear_values, get_handout_roster
from apps.warband.item.services.shop import annotate_stored_copy_counts
from apps.warband.quest.models.quest import Quest
from apps.warband.savegame.mixins import (
    PlayerFactionScopedQuerysetMixin,
    RunningSavegameRequiredMixin,
    SavegameScopedQuerysetMixin,
)
from apps.warband.savegame.models.savegame import Savegame
from apps.warband.savegame.services.current_savegame import get_current_savegame_for_request
from apps.warband.skirmish.messages.commands.skirmish import AttackFaction
from apps.warband.skirmish.models.skirmish import Skirmish
from apps.warband.skirmish.models.warrior import Warrior
from apps.warband.town.buildings.hall import Hall
from apps.warband.warrior.domain.knowledge import WarriorKnowledge
from apps.warband.warrior.services.dismissal import get_dismissal_refusals
from apps.warband.warrior.services.unpaid_wages import get_unpaid_wages_note


class PlayerFactionAwareContextMixin:
    """
    Tells the template whether the faction it is rendering belongs to the player, and what that makes
    the men standing on its pages.

    The faction detail page serves the player's own faction and a rival's alike, and so do the htmx
    partials that replace parts of it. All of those renderings have to answer this the same way: the
    partials carry controls only the player's own faction may use and address him about property
    that may not be his, so a page that got the answer right once and lost it on the first
    "loadFactionItemList" swap would put the rival's Sell button back.

    The two knowledge levels ride along for exactly that reason - see
    docs/patterns/warrior-knowledge.md. A roster is the faction's own war band and a captive list or
    a pub is men it holds, so the page's answer settles both, and a swap cannot disagree with the
    page it swapped into.
    """

    current_savegame: Savegame = None

    def setup(self, request, *args, **kwargs) -> None:
        # Resolved once here rather than in every method needing it, the way RivalFactionListView
        # does: the answer cannot change within one render
        super().setup(request, *args, **kwargs)
        self.current_savegame = get_current_savegame_for_request(request=request)

    def get_context_data(self, **kwargs) -> dict:
        context = super().get_context_data(**kwargs)
        # A savegame without a player faction gives None here, which no faction id equals - so it
        # renders as a rival's page, which is right: there is no own faction yet.
        context["is_player_faction"] = self.object.id == self.current_savegame.player_faction_id
        # The men on this page, as the player stands to them. A rival's roster, a rival's cells and a
        # rival's pub are all one thing to him - somebody else's - so both keys collapse to RIVAL
        # there rather than each page picking its own word for it.
        context["roster_knowledge"] = (
            WarriorKnowledge.COMMANDED if context["is_player_faction"] else WarriorKnowledge.RIVAL
        )
        context["held_knowledge"] = WarriorKnowledge.HELD if context["is_player_faction"] else WarriorKnowledge.RIVAL
        return context


class FactionRosterContextMixin:
    """
    Assembles the roster a faction page renders.

    Read by the pages that show the men as cards and by the progress table that says where each of
    them stands, so the two can never describe different war bands or disagree about their order.
    """

    def get_context_data(self, **kwargs) -> dict:
        context = super().get_context_data(**kwargs)

        # The row names the weapon and the armour a man stands in, and an item's name reads its type,
        # so all four come along in the one query rather than in up to four per man. The faction too:
        # the row names the man in full, and that asks whether he holds its seat.
        #
        # By name, and the id only to break a tie between two men of the same one: the progress table
        # reads the same list, and a warrior's own page walks it with Previous and Next - so an
        # unordered roster would be three screens disagreeing about who comes after whom.
        context["warrior_list"] = list(
            Warrior.objects.select_related("weapon__type", "armor__type", "faction")
            .with_portrait()
            .exclude_dead()
            .filter_faction(faction_id=self.object.id)
            .order_by("name", "id")
        )

        return context


class RosterDismissalContextMixin(FactionRosterContextMixin):
    """
    Says of each man on the roster whether he may be sent away, and where he stands on his wages.

    Shared by the roster page and the htmx partial that replaces its warrior list, because a roster
    the player got a Dismiss control on once and lost on the first "loadFactionWarriorList" swap is
    the same defect [PlayerFactionAwareContextMixin] exists to prevent.

    The refusals come off the one service the dismiss view asks before it dispatches, so a control
    the card offers and a click the view accepts cannot come apart. Asked once for the whole roster
    rather than per card - see "get_dismissal_refusals" - and only for the player's own faction: a
    rival's men carry no control to explain, and the balance being weighed would be the wrong purse.
    The wage note is gated on the same answer, for the same reason the card withholds health and
    morale: a rival's wage troubles are knowledge the player has not earned.

    Both are attached to each warrior rather than handed over as dicts, because the card is rendered
    per warrior and a template cannot index a dict by a variable key.

    Separate from the plain roster above because the progress table renders neither control and the
    two answers cost a warrior query and a balance query to reach.
    """

    def get_context_data(self, **kwargs) -> dict:
        context = super().get_context_data(**kwargs)

        if context["is_player_faction"]:
            player_faction = self.current_savegame.player_faction
            refusals = get_dismissal_refusals(
                faction=player_faction,
                warrior_list=context["warrior_list"],
                month=self.current_savegame.current_month,
                balance=Transaction.objects.current_balance(faction_id=self.current_savegame.player_faction_id),
            )
            for warrior in context["warrior_list"]:
                warrior.dismissal_refusal = refusals.get(warrior.id)
                # The leader is handed over rather than read off the warrior's own faction, which
                # would be a query per card for a number the page already holds
                warrior.unpaid_wages_note = get_unpaid_wages_note(warrior=warrior, leader_id=player_faction.leader_id)

        return context


class HandoutRosterContextMixin(PlayerFactionAwareContextMixin):
    """
    The men an unused item may be handed to, for every page that renders the stores column.

    Read here rather than off the faction in the template, because the list has a rule in it now: a
    man standing in a fight nobody has settled fights on with what he marched out with, so handing
    him something would be a control that could only ever be refused - and the refusal lives in
    "get_equip_refusal", which the assign view asks before it dispatches.

    Once for the whole column rather than once per card, the same reason
    "RosterDismissalContextMixin" asks its own question a roster at a time: the stores page renders a
    card per unused item and they all offer the same roster. Each man arrives carrying what his slots
    are worth, so an option can say whether the item on offer beats what it would displace without
    the empty case costing a query - see "annotate_held_gear_values".

    Only for the player's own faction. A rival's stores page carries no controls at all, so the
    roster behind them is a query for a picker nobody is shown.
    """

    def get_context_data(self, **kwargs) -> dict:
        context = super().get_context_data(**kwargs)

        context["handout_roster"] = get_handout_roster(faction=self.object) if context["is_player_faction"] else []

        return context


class PlayerFactionMixin(PlayerFactionScopedQuerysetMixin):
    """
    Resolves the one faction the current player commands.

    The url carries no id, so the scoped queryset holds exactly that faction - and nothing at all
    before the player has an active savegame with a faction, which is a page with no subject rather
    than a server error. The same shape as "PlayerTownMixin".

    Both of the sections that are the player's own stand on this: the war band's five pages, which
    read his men and his gear, and the town's three, which read what his town is offering him this
    month. Whose faction it is, is one question however many pages ask it.
    """

    model = Faction

    def get_object(self, queryset=None) -> Faction:
        # Going through "self" rather than "super()" is what keeps the scoping applied
        faction = self.get_queryset().first()
        if faction is None:
            raise Http404("The current savegame has no war band.")

        return faction


class FactionDetailView(
    FactionRosterContextMixin, HandoutRosterContextMixin, SavegameScopedQuerysetMixin, generic.DetailView
):
    """
    A rival's page: who he has, what he owns, who he holds, and whether the player may march on him.

    The player's own war band is five pages of its own, and this url is where every link to it used
    to point - a bookmark, a fight report, the counter in the bar. Rather than answering those with a
    404 or with a second copy of the roster, the one id that is his own is sent to the page that now
    holds it.
    """

    model = Faction
    template_name = "faction/faction_detail.html"

    def get(self, request, *args, **kwargs) -> HttpResponse:
        if self.current_savegame is not None and self.kwargs["pk"] == self.current_savegame.player_faction_id:
            return HttpResponseRedirect(reverse("warband:warband-roster-view"))

        return super().get(request, *args, **kwargs)

    def get_context_data(self, **kwargs):
        context = super().get_context_data(**kwargs)

        current_savegame = self.current_savegame
        # A button that simply vanishes teaches the player nothing, and "every warrior fights once a
        # month" is the rule he is most likely to walk into without noticing. Several things can take
        # the button away, so each gets its own sentence - and all of them come off the one service the
        # rivals list reads, so the two pages cannot word the rule differently.
        attack_standing = get_attack_standing(savegame=current_savegame)
        attack_refusal = attack_standing.refusals.get(self.object.id)
        context["can_be_attacked"] = self.object.id in attack_standing.attackable_rival_ids
        context["has_marched_this_month"] = attack_refusal == AttackRefusal.HAS_MARCHED_THIS_MONTH
        context["leader_cannot_march"] = attack_refusal == AttackRefusal.LEADER_CANNOT_MARCH
        context["their_war_band_is_committed"] = attack_refusal == AttackRefusal.WAR_BAND_IS_COMMITTED
        # The opposite question to the three above, and the only one of the four that offers the
        # player something rather than explaining an absence: this rival has nobody left to hold his
        # town. Asked through the same queryset FactionOccupyView resolves its target with, so the
        # button and the page it leads to cannot disagree. No month, and nothing about the player's
        # own leader - see "occupiable_by".
        context["can_be_occupied"] = (
            Faction.objects.occupiable_by(savegame=current_savegame).filter(id=self.object.id).exists()
        )
        # The first of the three explanations, and the one that outranks the other two: a decided
        # savegame is why no war band of his is marching, and the month it happens to be in is beside
        # the point. Not asked about the two offers above - "attackable_by" and "occupiable_by" both
        # hold the same guard, so a second one here would answer a question they have settled.
        context["savegame_is_over"] = current_savegame.is_over

        return context


class WarbandRosterView(
    RosterDismissalContextMixin, PlayerFactionAwareContextMixin, PlayerFactionMixin, generic.DetailView
):
    """
    The men the player commands, and what the war band itself is.

    Where the Warband entry lands. The faction's name, its culture and its leader sit in the heading
    rather than on a page of their own: three values and no action is what a page is headed with, not
    what it is about.
    """

    template_name = "faction/warband_roster.html"


class WarbandStoresView(HandoutRosterContextMixin, PlayerFactionMixin, generic.DetailView):
    """What nobody is wearing, which is also what can be sold."""

    template_name = "faction/warband_stores.html"


class WarbandFyrdView(PlayerFactionMixin, generic.DetailView):
    """The levy the player can draft another man out of this month."""

    template_name = "faction/warband_fyrd.html"


class WarbandCaptivesView(PlayerFactionAwareContextMixin, PlayerFactionMixin, generic.DetailView):
    """The prisoners the player holds, to recruit or to sell."""

    template_name = "faction/warband_captives.html"


class WarbandProgressView(FactionRosterContextMixin, PlayerFactionMixin, generic.DetailView):
    """
    Where each man stands on the four attributes a month of training moves.

    Reads the plain roster: the table renders no control, so the dismissal refusals and the wage
    notes would be two queries for something nobody looks at.
    """

    template_name = "faction/warband_progress.html"


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
        self.current_savegame = get_current_savegame_for_request(request=request)

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
            # still comes back. His own faction rides along because naming him by his title asks it.
            .select_related("culture", "leader__faction")
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

        # The same answer the faction page reads for its one rival, asked once for the whole table
        attack_standing = get_attack_standing(savegame=self.current_savegame)
        # Asked once for the whole page as well, for the same reason: a lookup per row is a query per
        # row. Not the complement of the attackable set - a rival can be out of it while its healthy
        # men are merely spoken for elsewhere, and that town is still defended.
        occupiable_rival_ids = set(
            Faction.objects.occupiable_by(savegame=self.current_savegame).values_list("id", flat=True)
        )

        # Evaluated into a list, because the template iterating the queryset again would re-run it and
        # lose these answers
        rival_list = list(context[self.context_object_name])
        for rival in rival_list:
            rival.can_be_attacked = rival.id in attack_standing.attackable_rival_ids
            rival.can_be_occupied = rival.id in occupiable_rival_ids
            rival.their_war_band_is_committed = (
                attack_standing.refusals.get(rival.id) == AttackRefusal.WAR_BAND_IS_COMMITTED
            )
        context[self.context_object_name] = rival_list

        # The first of the facts about the player, and the one that outranks the other two: a
        # decided savegame is why no war band of his is marching, and the month it happens to be in
        # is beside the point.
        context["savegame_is_over"] = self.current_savegame.is_over
        # Said once above the table rather than on every row: both are facts about the player's own
        # war band, so no rival is what decides them, and a row each would be the same sentence
        # repeated as many times as there are rivals. Only said at all while somebody is still
        # standing - over a board that has been cleared it explains the absence of a button that
        # nothing would have offered anyway, which is what "war_band_refusal" being None there means.
        context["has_marched_this_month"] = attack_standing.war_band_refusal == AttackRefusal.HAS_MARCHED_THIS_MONTH
        context["leader_cannot_march"] = attack_standing.war_band_refusal == AttackRefusal.LEADER_CANNOT_MARCH

        return context


class FactionItemListView(HandoutRosterContextMixin, SavegameScopedQuerysetMixin, generic.DetailView):
    model = Faction
    template_name = "faction/item/components/item_list.html"


class FactionPubMercenaryListView(PlayerFactionAwareContextMixin, SavegameScopedQuerysetMixin, generic.DetailView):
    """
    The pub's own htmx partial, so hiring the last mercenary can leave a sentence behind.

    Scoped to the savegame rather than to the player faction, the same as the town square that holds
    it: the page is reachable for any faction of the savegame, and the pub is what that page shows.
    Hiring stays the player's own - "RecruitPubMercenaryView" scopes that to his pub.

    Which is why it has to know whose pub it is rendering. Reachable for any faction means a rival's
    faction id in the url reaches a rival's pub, and men the player cannot hire are men he has not
    been offered - so the card that fuzzes a mercenary's numbers for him has to withhold the gear it
    would otherwise be advertising on somebody else's behalf.
    """

    model = Faction
    template_name = "faction/warrior/components/pub_mercenary_list.html"


class FactionWarriorListView(
    RosterDismissalContextMixin, PlayerFactionAwareContextMixin, SavegameScopedQuerysetMixin, generic.DetailView
):
    model = Faction
    template_name = "faction/warrior/components/warrior_list.html"


class FactionCapturedWarriorListView(PlayerFactionAwareContextMixin, SavegameScopedQuerysetMixin, generic.DetailView):
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
        current_savegame: Savegame = get_current_savegame_for_request(request=self.request)

        handle_message(DraftWarriorFromFyrd(faction=obj, month=current_savegame.current_month))
        response = render(request, self.template_name, {"faction": obj})

        response["HX-Trigger"] = json.dumps(
            {
                "notification": "New Warrior drafted",
                "loadFactionWarriorList": "-",
                "loadFactionItemList": "-",
                "updateResourceBar": "-",
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
    the men who walked out on a rival, all of whom would otherwise be hireable by id, and most of them
    for nothing.

    The URL carries the warrior only. Which pub he is taken from is the player's, read off the
    savegame, because the player hires from his own town - a posted faction could only ever lie about
    that.
    """

    model = Warrior
    http_method_names = ("post",)

    def get_queryset(self) -> QuerySet:
        current_savegame: Savegame = get_current_savegame_for_request(request=self.request)
        if current_savegame is None or current_savegame.player_faction_id is None:
            return super().get_queryset().none()

        return super().get_queryset().in_pub_of(faction_id=current_savegame.player_faction_id)

    def post(self, *args, **kwargs):
        obj = self.get_object()
        current_savegame: Savegame = get_current_savegame_for_request(request=self.request)

        # Read once, and before the message goes out: hiring him ends the wait his price is partly
        # made of, and the handler clears it on this very instance - so a second read afterwards
        # would tell the player a figure the ledger never charged. See [Warrior.idle_surcharge].
        hiring_price = obj.hiring_price

        refusal = get_pub_hire_refusal(faction=current_savegame.player_faction, hiring_price=hiring_price)
        if refusal is not None:
            response = HttpResponse(status=HTTPStatus.NO_CONTENT)
            response["HX-Trigger"] = json.dumps({"notification": refusal})
            return response

        handle_message(
            RecruitPubMercenary(
                warrior=obj,
                faction=current_savegame.player_faction,
                month=current_savegame.current_month,
            )
        )

        # The body is the way on to the man, appended above the pub rather than swapped in place of
        # his card: the pub list reloads itself on "loadPubMercenaryList", which is what renders its
        # empty state when the man just hired was the last one in it, and a line inside the list
        # would go with the reload. The line names the man and his price, so a toast would only
        # repeat it.
        response = render(
            self.request,
            "faction/warrior/components/pub_hired_row.html",
            {
                "warrior": obj,
                "hiring_price": hiring_price,
            },
        )
        response["HX-Trigger"] = json.dumps(
            {
                "loadPubMercenaryList": "-",
                "updateResourceBar": "-",
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
        self.current_savegame = get_current_savegame_for_request(request=request)
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

        return super().get_queryset().attackable_by(savegame=self.current_savegame)

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
        # Said before the march, from the same answer the march itself is staged with
        context["fortification_strength"] = self.object.town.get_fortification_strength()
        context["successor"] = self.current_savegame.player_faction.get_successor()
        return context

    def form_valid(self, form):
        # The march before the response, because the response is the fight it creates:
        # "super().form_valid" is what asks "get_success_url", and that reads the skirmish back out
        # of the database. Dispatching afterwards would send the player to a row that did not exist
        # when the redirect was built.
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

        return super().form_valid(form)

    def get_success_url(self):
        """
        The fight the march just started, not the list of every fight there has ever been.

        Read back out of the database rather than handed over: "handle_message" drains the queue and
        returns nothing, so the skirmish the chain created is not a value this view ever holds. The
        three columns below name exactly one row - a war band marches once a month, whoever leads it
        (see "Faction.has_marched_this_month"), so there cannot be a second march on the same rival in
        the same month for this to pick the wrong one of.

        Unguarded against finding nothing, on purpose. "handle_create_skirmish_for_attack" stages the
        fight unconditionally, and the whole chain runs inside one transaction, so a march that
        reached this line created a skirmish - and one that did not rolled back and never got here.
        A fallback to the list would be a branch no test could reach.
        """
        skirmish = Skirmish.objects.filter(
            attacking_faction=self.current_savegame.player_faction,
            defending_faction=self.object,
            month=self.current_savegame.current_month,
        ).latest("id")

        return reverse("warband:skirmish-fight-view", kwargs={"pk": skirmish.id})


class FactionOccupyView(RunningSavegameRequiredMixin, SingleObjectMixin, generic.View):
    """
    Rides into a rival town that has nobody healthy left to hold it.

    Carries no scoping mixin, for the same reason FactionAttackView does not: every rule about who may
    be ridden into - the savegame among them - lives in "occupiable_by()", and a second, looser scope
    on top would only invite the two to disagree. A rival who is still standing is simply not found.

    POST only and no form: there is nothing to compose. The war band that opened the window has
    already marched, so the occupation takes no warriors and offers no choices - it is one button.
    """

    model = Faction
    http_method_names = ("post",)

    def get_queryset(self) -> QuerySet:
        current_savegame: Savegame = Savegame.objects.get_current_savegame(user_id=self.request.user.id)
        if current_savegame is None:
            return super().get_queryset().none()

        return super().get_queryset().occupiable_by(savegame=current_savegame)

    def post(self, request, *args, **kwargs):
        obj = self.get_object()
        current_savegame: Savegame = Savegame.objects.get_current_savegame(user_id=request.user.id)

        handle_message(
            OccupyFaction(
                # The scoped object from the URL, not a posted field: which town is ridden into is
                # decided by the route that was allowed to be reached
                faction=obj,
                occupying_faction=current_savegame.player_faction,
                month=current_savegame.current_month,
            )
        )

        # A message rather than an "HX-Trigger": this is a plain post answered with a redirect, so the
        # browser navigates away and nothing is left to read a header. base.html renders "messages" on
        # every page, so the same toast comes out the other end.
        messages.add_message(request, messages.SUCCESS, f"You ride into {obj.town_name}. {obj} is finished.")

        # Back to the rival list rather than to the town just taken: the faction is knocked out, and
        # its page is the one thing the player has no further use for
        return HttpResponseRedirect(reverse("warband:rival-faction-list-view"))


class MonthlyCostOverview(SavegameScopedQuerysetMixin, generic.DetailView):
    model = Faction
    template_name = "faction/faction/components/current_cost_card.html"

    def get_context_data(self, **kwargs):
        context = super().get_context_data(**kwargs)
        # Fetch current savegame record
        current_savegame: Savegame = get_current_savegame_for_request(request=self.request)

        # The wage bill itself is not assembled here. It comes off "wage_bill_payroll", the same
        # projection the salary run bills from and the navbar warns from, which the finance context
        # processor puts on every render - computing it here again is what made the card and the
        # month disagree about who goes unpaid. Only the income is this card's own, because it is
        # the one number on it that nothing else shows - and it is the faction's own figure, the one
        # the month pays out, rather than assembled from a building here.
        hall = Hall.get_building_by_type(building_type=current_savegame.player_faction.town.hall)

        context["building_income_amount"] = current_savegame.player_faction.get_monthly_income()
        # What the hall would pay fully manned, and what fully manned takes. A hall paying a share
        # because the war band is short of it is a rule the player has to be able to see on the page
        # where he reads what the month will do to his purse - the alternative is silver going
        # missing every month for a reason nothing names.
        context["building_income_full_amount"] = hall.REVENUE_PER_ROUND
        context["warriors_for_full_income"] = hall.WARRIORS_FOR_FULL_REVENUE

        return context


class ShopShelfContextMixin:
    """
    The shelf, each item carrying how many of its kind already lie unused in the stores, and the men
    it is weighed against, for both the shop page and the list that replaces itself after every
    purchase - the two have to agree or the first purchase changes what the cards say.

    The stores are the faction's own whose shop this is. The page only ever renders the player's; the
    partial is reachable for any faction of the savegame, and a rival's shelf then reads a rival's
    stores rather than telling the player about gear that is not his.
    """

    def get_context_data(self, **kwargs) -> dict:
        context = super().get_context_data(**kwargs)
        context["item_list"], context["stored_item_count"] = annotate_stored_copy_counts(
            item_list=self.object.available_items.select_related("type"), faction=self.object
        )
        # Every living man rather than the handout roster: a man standing in an open fight cannot be
        # handed gear today, but he is back next month and the sword is bought for the band, not for
        # this afternoon. Read once for the shelf, so a card saying it improves nobody costs no query.
        context["gear_roster"] = annotate_held_gear_values(roster=self.object.get_all_living_warriors())
        return context


class TownShopView(ShopShelfContextMixin, PlayerFactionMixin, generic.DetailView):
    """
    The gear on the stalls this month, which is where the Town entry lands.

    Carries no "PlayerFactionAwareContextMixin": the shop's list reads the items and the faction's id
    and asks nothing about whose they are. Every man it could arm is the player's, because the page
    has no id to be pointed anywhere else.
    """

    model = Faction
    template_name = "faction/town_shop.html"


class TownPubView(PlayerFactionAwareContextMixin, PlayerFactionMixin, generic.DetailView):
    """
    The men drinking in the player's own pub, to hire or to leave standing.

    It answers whose pub this is for the same reason "FactionPubMercenaryListView" does, and the two
    have to agree or the first "loadPubMercenaryList" swap changes what the cards give away. The
    partial is still reachable for any faction of the savegame; this page is not, so its answer here
    is always the player's own.
    """

    model = Faction
    template_name = "faction/town_pub.html"


class TownBoardView(PlayerFactionMixin, generic.DetailView):
    """What is pinned to the board this month, and still open to be taken on."""

    model = Faction
    template_name = "faction/town_board.html"

    def get_context_data(self, **kwargs):
        context = super().get_context_data(**kwargs)
        # Asked through the same queryset QuestAcceptView resolves its quest with, so a card is only
        # ever shown for a quest that can actually be taken on. Every row names the faction it marches
        # on, so that comes along in the same query rather than in one per quest.
        context["quest_list"] = (
            Quest.objects.for_player_faction(faction_id=self.object.id)
            .resolvable(month=self.object.savegame.current_month)
            .select_related("target_faction")
        )
        return context


class FactionShopItemListView(ShopShelfContextMixin, SavegameScopedQuerysetMixin, generic.DetailView):
    model = Faction
    template_name = "faction/item/components/shop_item_list.html"


class ResourceBarHtmxView(generic.TemplateView):
    """
    Re-renders the navbar's three counters after an action has moved one of them.

    Read-only, so it deliberately carries no scoping mixin and no RunningSavegameRequiredMixin: it
    resolves nothing by id, and a finished savegame still has a navbar. Everything it shows comes from
    the context processors that run on every authenticated render, which is why there is no
    get_context_data here - and why they are the ones that answer for a user with no savegame yet.
    """

    template_name = "faction/components/resource_bar.html"
