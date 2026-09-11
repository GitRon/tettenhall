import json
from http import HTTPStatus

from django.db.models import QuerySet
from django.http import Http404, HttpResponse
from django.shortcuts import get_object_or_404, render
from django.urls import reverse
from django.views import generic
from queuebie.runner import handle_message

from apps.warband.faction.models.faction import Faction
from apps.warband.finance.models import Transaction
from apps.warband.savegame.mixins import (
    PlayerFactionScopedQuerysetMixin,
    RunningSavegameRequiredMixin,
    SavegameScopedQuerysetMixin,
)
from apps.warband.savegame.models.savegame import Savegame
from apps.warband.savegame.services.current_savegame import get_current_savegame_for_request
from apps.warband.skirmish.models.warrior import Warrior
from apps.warband.warrior.forms.warrior import WarriorForm
from apps.warband.warrior.messages.commands.warrior import (
    DismissWarrior,
    EnslaveCapturedWarrior,
    RecruitCapturedWarrior,
)
from apps.warband.warrior.services.dismissal import get_dismissal_refusals
from apps.warband.warrior.services.unpaid_wages import get_unpaid_wages_note


class WarriorDetailView(SavegameScopedQuerysetMixin, generic.DetailView):
    """
    One man, and the way back to the list he was read off.

    The page carried no navigation of its own at all, so equipping a second warrior meant going
    through the section nav and the roster again for every one of them. The roster link and the two
    neighbours below are what make a roster walkable - see docs/patterns/navigation.md.
    """

    model = Warrior
    template_name = "warrior/warrior_detail.html"

    def _add_roster_context(self, *, context: dict, player_faction: Faction | None) -> None:
        """
        Names the list this man was read off, and who stands either side of him in it.

        Three lists lead here and they are not the same roster: a faction's own men, the prisoners a
        faction holds, and the mercenaries standing in its pub. Which one he is in also decides which
        section of the game his page belongs to, because the url carries only his own id.
        """
        if self.object.faction_id:
            context["nav_section"] = "warband" if context["is_player_faction"] else "rivals"
            context["roster_label"] = f"Back to {self.object.faction}"
            context["roster_url"] = reverse("warband:faction-detail-view", args=[self.object.faction_id])
            roster = Warrior.objects.exclude_dead().filter_faction(faction_id=self.object.faction_id)
        elif context["is_captive_of_player"]:
            context["nav_section"] = "warband"
            context["roster_label"] = "Back to your captives"
            context["roster_url"] = reverse("warband:faction-detail-view", args=[player_faction.id])
            roster = player_faction.captured_warriors.all()
        elif context["is_mercenary_of_player"]:
            context["nav_section"] = "town"
            context["roster_label"] = "Back to the pub"
            context["roster_url"] = reverse("warband:town-square-view", args=[player_faction.id])
            roster = player_faction.available_mercenaries.all()
        else:
            # A dead man, or somebody the player reached by typing an id. Nothing to walk and no
            # section to claim.
            context["nav_section"] = None
            context["roster_label"] = None
            context["roster_url"] = None
            return

        # By name, because that is the only order a player can predict, and the roster the link above
        # leads to is read in the same one. The id breaks a tie between two men of the same name.
        roster_ids = list(roster.order_by("name", "id").values_list("id", flat=True))
        # He is off his own roster when he is dead: the lists all leave the dead out, and a "next"
        # that walked into a list he is not on would be a walk he cannot come back from.
        position = roster_ids.index(self.object.id) if self.object.id in roster_ids else None
        context["previous_warrior_id"] = roster_ids[position - 1] if position else None
        context["next_warrior_id"] = (
            roster_ids[position + 1] if position is not None and position + 1 < len(roster_ids) else None
        )

    def get_context_data(self, **kwargs) -> dict:
        context = super().get_context_data(**kwargs)
        # This page is where a rival card's "Detail" link leads, so it has to withhold the gear that
        # card withholds - otherwise hiding it one screen earlier only costs the player a click.
        #
        # Asked as "may the player see this man's gear", not "is he in the player's faction": the two
        # come apart for everybody carrying no faction at all. His own prisoners and the mercenaries
        # standing in his own pub are faction-less, and the pub card already advertises the weapon it
        # is charging him for - so a faction test would have hidden, one click later, what the town
        # square had just shown him.
        current_savegame = get_current_savegame_for_request(request=self.request)
        player_faction = current_savegame.player_faction if current_savegame else None
        # Seeing and changing are different rights, and a prisoner and a pub mercenary sit between
        # them: the player may read what they carry, but only his own men can be re-equipped - the
        # update view resolves nobody else. Rendering the edit control for them would be exactly the
        # control-that-can-only-fail this batch removed twice already.
        #
        # Named the way the roster card names it, because the page now withholds the same three
        # things the card withholds - health, morale and condition - and one predicate has to decide
        # both or a rival's numbers leak on whichever screen was updated second.
        context["is_player_faction"] = player_faction is not None and self.object.faction_id == player_faction.id
        context["can_edit_gear"] = context["is_player_faction"]
        # Asked once and kept, because the roster context below needs the same two answers to say
        # which list this man was read off
        context["is_captive_of_player"] = (
            player_faction is not None and player_faction.captured_warriors.filter(id=self.object.id).exists()
        )
        context["is_mercenary_of_player"] = (
            player_faction is not None and player_faction.available_mercenaries.filter(id=self.object.id).exists()
        )
        context["can_see_gear"] = (
            context["can_edit_gear"] or context["is_captive_of_player"] or context["is_mercenary_of_player"]
        )
        # Where the man stands on his wages, behind the same gate for the same reason: it is read off
        # his own morale being stuck, which a rival's card does not give away either. Carried here as
        # well as on the card, because the card links to this page and a page showing less about a man
        # than the tile clicked to reach it is what the gear rows above exist to correct.
        context["unpaid_wages_note"] = (
            get_unpaid_wages_note(warrior=self.object, leader_id=player_faction.leader_id)
            if context["is_player_faction"]
            else None
        )
        self._add_roster_context(context=context, player_faction=player_faction)
        return context


class WarriorWeaponUpdateView(PlayerFactionScopedQuerysetMixin, generic.UpdateView):
    # Changing what a warrior carries is a write, and being in the player's savegame is not enough:
    # a rival's men are in it too, and the URL was all it took to re-arm them
    model = Warrior
    form_class = WarriorForm
    template_name = "warrior/components/warrior_field_edit.html"
    object = None
    htmx_field = None

    def dispatch(self, request, *args, **kwargs):
        # The attribute is a free URL segment, and the form raises on anything it doesn't render -
        # which is a 404, not a server error
        self.htmx_field = kwargs.get("htmx_attribute")
        if self.htmx_field not in WarriorForm.Meta.fields:
            raise Http404("Unknown warrior attribute.")

        return super().dispatch(request, *args, **kwargs)

    def get_form_kwargs(self):
        kwargs = super().get_form_kwargs()
        kwargs["htmx_field"] = self.htmx_field
        return kwargs

    def form_valid(self, form):
        self.object = form.save()
        return render(self.request, "warrior/components/warrior_field_display.html", self.get_context_data())

    def get_context_data(self, **kwargs):
        context = super().get_context_data(**kwargs)
        context["object"] = self.object
        context["attribute"] = self.htmx_field
        context["field_value"] = getattr(self.object, self.htmx_field)
        # This view resolves the player's own men and nobody else, so anything it re-renders is
        # editable by construction - without this the control removes itself after one use
        context["can_edit_gear"] = True
        return context


class DismissWarriorView(RunningSavegameRequiredMixin, PlayerFactionScopedQuerysetMixin, generic.DetailView):
    """
    Sends a warrior off the player's roster and into the pub, stripped of the gear he was carrying.

    Only the player's own men, so the savegame is not scope enough: a rival's warriors are in it too,
    and the id from the URL was all it would take to empty a rival's war band for him - or to bill
    the player severance for doing it.

    The dead are narrowed away rather than refused. Death leaves a man on the roster but off the
    page, he draws no wages, and there is nothing about him for a dismissal to fix - so a post naming
    one is a 404 rather than a sentence explaining itself.
    """

    model = Warrior
    http_method_names = ("post",)

    def get_queryset(self) -> QuerySet:
        return super().get_queryset().exclude_dead()

    def post(self, request, *args, **kwargs) -> HttpResponse:
        obj = self.get_object()
        current_savegame: Savegame = get_current_savegame_for_request(request=self.request)
        player_faction = current_savegame.player_faction

        # The same function the card asks before it offers the control, so a refusal here means the
        # page the player clicked from was stale rather than that the two disagree
        refusal = get_dismissal_refusals(
            faction=player_faction,
            warrior_list=[obj],
            month=current_savegame.current_month,
            balance=Transaction.objects.current_balance(faction_id=player_faction.id),
        ).get(obj.id)

        if refusal is not None:
            response = HttpResponse(status=HTTPStatus.NO_CONTENT)
            response["HX-Trigger"] = json.dumps({"notification": refusal})
            return response

        severance_pay = obj.severance_pay
        handle_message(
            DismissWarrior(
                warrior=obj,
                faction=player_faction,
                savegame=current_savegame,
                month=current_savegame.current_month,
            )
        )

        response = HttpResponse(status=HTTPStatus.OK)
        response["HX-Trigger"] = json.dumps(
            {
                "notification": f"{obj} leaves your war band for {severance_pay} silver. He waits in the pub.",
                # The gear he leaves behind is what the player sells to raise silver, so the item list
                # has to come back with it on the shelf
                "loadFactionWarriorList": "-",
                "loadFactionItemList": "-",
                "updateResourceBar": "-",
            }
        )
        return response


class CapturedWarriorActionMixin(SavegameScopedQuerysetMixin):
    """
    Resolves the player's own faction as the one holding a captured warrior.

    Two facts have to be verified, and the savegame is not enough for either. The faction id arrives in
    the URL, so it could name a rival of this very savegame - and a rival is a faction the player may
    not act for: recruiting a rival's captive staffs the rival's war band for free, and enslaving one
    pays the rival for his own prisoner. And "remove_captive()" is a silent no-op for a warrior that was
    never captured, so without the membership check a player could enslave his own warriors for silver.
    """

    def get_captor_faction(self, *, warrior: Warrior) -> Faction:
        current_savegame: Savegame = get_current_savegame_for_request(request=self.request)
        if current_savegame is None or current_savegame.player_faction_id is None:
            raise Http404

        return get_object_or_404(
            Faction.objects.for_player_faction(faction_id=current_savegame.player_faction_id).filter(
                captured_warriors=warrior
            ),
            pk=self.kwargs["faction_id"],
        )


class WarriorRecruitCapturedView(RunningSavegameRequiredMixin, CapturedWarriorActionMixin, generic.DetailView):
    model = Warrior
    http_method_names = ("post",)

    def post(self, request, *args, **kwargs):
        obj = self.get_object()
        faction = self.get_captor_faction(warrior=obj)
        current_savegame: Savegame = get_current_savegame_for_request(request=self.request)

        handle_message(RecruitCapturedWarrior(faction=faction, warrior=obj, month=current_savegame.current_month))

        response = HttpResponse(status=HTTPStatus.OK)
        response["HX-Trigger"] = json.dumps(
            {
                "notification": "Captured warrior joined your ranks",
                "loadFactionWarriorList": "-",
                "loadFactionCapturedWarriorList": "-",
                "updateResourceBar": "-",
            }
        )

        return response


class WarriorEnslaveCapturedView(RunningSavegameRequiredMixin, CapturedWarriorActionMixin, generic.DetailView):
    model = Warrior
    http_method_names = ("post",)

    def post(self, request, *args, **kwargs):
        obj = self.get_object()
        faction = self.get_captor_faction(warrior=obj)
        current_savegame: Savegame = get_current_savegame_for_request(request=self.request)

        handle_message(EnslaveCapturedWarrior(faction=faction, warrior=obj, month=current_savegame.current_month))

        response = HttpResponse(status=HTTPStatus.OK)
        response["HX-Trigger"] = json.dumps(
            {
                "notification": "Captured warrior was sold into slavery",
                "loadFactionCapturedWarriorList": "-",
                "updateResourceBar": "-",
            }
        )

        return response
