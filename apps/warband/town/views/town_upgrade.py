from django.contrib import messages
from django.http import Http404
from django.urls import reverse
from django.views import generic
from queuebie.runner import handle_message

from apps.common.http import hx_redirect
from apps.warband.savegame.mixins import PlayerFactionScopedQuerysetMixin, RunningSavegameRequiredMixin
from apps.warband.savegame.models.savegame import Savegame
from apps.warband.savegame.services.current_savegame import get_current_savegame_for_request
from apps.warband.town.buildings import BUILDINGS
from apps.warband.town.buildings.hall import Hall
from apps.warband.town.messages.commands.town import ThrowFeast, UpgradeTownBuilding
from apps.warband.town.models import Town
from apps.warband.town.services.building_upgrade import (
    ALREADY_BUILT_THIS_MONTH_REFUSAL,
    UNAFFORDABLE_REFUSAL,
    get_building_upgrade_refusal,
)
from apps.warband.town.services.feast import (
    ALREADY_FEASTED_THIS_MONTH_REFUSAL,
    NO_HALL_REFUSAL,
    UNAFFORDABLE_FEAST_REFUSAL,
    get_feast_refusal,
)


class PlayerTownMixin(PlayerFactionScopedQuerysetMixin):
    """
    Resolves the single town the current player owns.

    The URL carries no id, so the scoped queryset holds exactly that town - and nothing at all
    before the player has an active savegame with a faction, which has to be a 404 rather than a
    server error.
    """

    def get_object(self, queryset=None) -> Town:
        # Going through "self" rather than "super()" is what keeps the scoping applied
        town = self.get_queryset().first()
        if town is None:
            raise Http404("The current savegame has no town.")

        return town


class TownUpgradeView(PlayerTownMixin, generic.DetailView):
    model = Town
    template_name = "town/town_upgrade.html"

    def get_context_data(self, **kwargs):
        town = self.object
        current_savegame: Savegame = get_current_savegame_for_request(request=self.request)

        context = super().get_context_data(**kwargs)

        building_list = []
        for building_type, building_class in BUILDINGS.items():
            current_level = getattr(town, building_type)
            max_level = building_class.get_max_level()
            # Capped at the maximum so the last level can still name a price instead of asking for a
            # variant above the largest one
            next_level = min(current_level + 1, max_level)
            is_at_max_level = current_level == max_level

            current_building = building_class.get_building_by_type(building_type=current_level)
            next_building = building_class.get_building_by_type(building_type=next_level)

            # The page asks the same question the upgrade does, so a button can never offer a building
            # the click would then refuse. At most one refusal comes back, month before price, which
            # is the order the buttons below are chosen in too.
            refusal = get_building_upgrade_refusal(
                town=town, building_type=building_type, current_savegame=current_savegame
            )

            level_display = town.get_building_level_display(building_type=building_type, level=current_level)
            next_level_display = town.get_building_level_display(building_type=building_type, level=next_level)

            building_list.append(
                {
                    "building_type": building_type,
                    "label": building_class.BUILDING_LABEL,
                    "level": current_level,
                    "level_display": level_display,
                    "max_level": max_level,
                    "next_level_display": next_level_display,
                    "costs": next_building.BUILDING_COSTS,
                    # What the money buys, level by level. The player is choosing between four prices,
                    # each paid for with months of men and gear he goes without, so the numbers are
                    # what the decision needs.
                    #
                    # An effect the next level answers with the same value is left out, because a row
                    # reading "1 -> 1" prices a lever that is not moving and nothing says a level has
                    # to move every effect its family declares. Only while there is an upgrade to
                    # describe: at the maximum level "next_building" is "current_building", every pair
                    # matches, and an unguarded filter would empty the card of the last level - which
                    # is the one level whose effects are the whole point of the card.
                    "effect_list": [
                        {"label": effect.label, "current": effect.value, "next": upgraded_effect.value}
                        for effect, upgraded_effect in zip(
                            current_building.get_effects(), next_building.get_effects(), strict=True
                        )
                        if is_at_max_level or effect.value != upgraded_effect.value
                    ],
                    "has_already_built": refusal == ALREADY_BUILT_THIS_MONTH_REFUSAL,
                    # Answering a click with a warning that fades after a second is no way to price a
                    # building, so an unaffordable one says so on the button instead
                    "can_afford": refusal != UNAFFORDABLE_REFUSAL,
                }
            )

        context.update({"building_list": building_list})

        # The feast sits on the same page as the hall it is thrown in, priced for the war band as it
        # stands, so the player reads the whole bill before he clicks rather than after. The card asks
        # the refusal the feast itself asks, so a button can never offer a feast the click would refuse
        hall = Hall.get_building_by_type(building_type=town.hall)
        head_count = town.faction.warriors.exclude_dead().count()
        feast_refusal = get_feast_refusal(town=town, head_count=head_count, current_savegame=current_savegame)
        context.update(
            {
                "feast": {
                    "can_feast": feast_refusal != NO_HALL_REFUSAL,
                    "restored_percent": round(hall.FEAST_RESTORED_SHARE * 100),
                    "head_count": head_count,
                    "price_per_head": hall.FEAST_PRICE_PER_HEAD,
                    "costs": hall.get_feast_price(head_count=head_count),
                    "has_feasted": feast_refusal == ALREADY_FEASTED_THIS_MONTH_REFUSAL,
                    "can_afford": feast_refusal != UNAFFORDABLE_FEAST_REFUSAL,
                }
            }
        )

        return context


class UpgradeBuildingView(RunningSavegameRequiredMixin, PlayerTownMixin, generic.DetailView):
    model = Town
    http_method_names = ("post",)

    def post(self, request, *args, **kwargs):
        # The building arrives as a free string from the URL, and its name is what "getattr" and the
        # handler's "setattr" address on the town. Without this lookup posting "faction_id" would
        # hand the town to another faction.
        building_type = self.kwargs["building_type"]
        if building_type not in BUILDINGS:
            raise Http404(f"Unknown building type: {building_type}")

        town = self.get_object()
        current_savegame: Savegame = get_current_savegame_for_request(request=self.request)

        refusal = get_building_upgrade_refusal(
            town=town, building_type=building_type, current_savegame=current_savegame
        )
        if refusal is not None:
            messages.add_message(request, messages.WARNING, refusal)

            return hx_redirect(url=reverse("warband:town-upgrade-view"))

        new_level = getattr(town, building_type) + 1
        desired_building = BUILDINGS[building_type].get_building_by_type(building_type=new_level)

        handle_message(
            UpgradeTownBuilding(
                town=town,
                faction=town.faction,
                building_type=building_type,
                new_level=new_level,
                costs=desired_building.BUILDING_COSTS,
                month=current_savegame.current_month,
            )
        )
        messages.add_message(request, messages.SUCCESS, "Building upgraded.")

        return hx_redirect(url=reverse("warband:town-upgrade-view"))


class ThrowFeastView(RunningSavegameRequiredMixin, PlayerTownMixin, generic.DetailView):
    model = Town
    http_method_names = ("post",)

    def post(self, request, *args, **kwargs):
        town = self.get_object()
        current_savegame: Savegame = get_current_savegame_for_request(request=self.request)

        # The table is laid for the war band as it stands at the click: the living men under this
        # banner. A captive has no banner, so he is off the list without anybody having to say so
        warrior_list = list(town.faction.warriors.exclude_dead())

        refusal = get_feast_refusal(town=town, head_count=len(warrior_list), current_savegame=current_savegame)
        if refusal is not None:
            messages.add_message(request, messages.WARNING, refusal)

            return hx_redirect(url=reverse("warband:town-upgrade-view"))

        hall = Hall.get_building_by_type(building_type=town.hall)

        handle_message(
            ThrowFeast(
                town=town,
                faction=town.faction,
                warrior_list=warrior_list,
                restored_share=hall.FEAST_RESTORED_SHARE,
                costs=hall.get_feast_price(head_count=len(warrior_list)),
                month=current_savegame.current_month,
            )
        )
        messages.add_message(request, messages.SUCCESS, "The war band feasted in the hall.")

        return hx_redirect(url=reverse("warband:town-upgrade-view"))
