from dataclasses import dataclass

from django.db.models import Count, Q

from apps.warband.faction.models.faction import Faction
from apps.warband.quest.models import Quest
from apps.warband.skirmish.models import Skirmish, Warrior
from apps.warband.town.models import Town


@dataclass(frozen=True, kw_only=True)
class WarbandStanding:
    """
    What shape the war band is in, in the four numbers a month is decided against.

    A summary and deliberately not a roster: the faction page renders a card per man, and a second
    rendering of it here would cost a query per man on the page every month starts on. The counts
    below come out of one aggregate.

    The dead are left out of every count, the way the faction page leaves them off the roster and
    the navbar leaves them out of its warrior counter - a man who is gone is not a man in poor
    condition.
    """

    warrior_count: int
    unconscious_count: int
    fleeing_count: int
    # The player's own leader, so the page can name him. Nothing here is said about a rival's.
    leader: Warrior | None
    # Whether he may march this month, which is the question the attack button asks. A war band
    # whose leader is wounded, dead or already promised to a quest has no attack to launch at all,
    # and today the player only learns that by opening a rival's page.
    leader_can_march: bool
    # Neither of these expires when the month turns, which is why they are two lines here rather
    # than rows on the panel of things that do.
    fyrd_reserve: int
    captive_count: int

    @property
    def is_intact(self) -> bool:
        """Whether every man still standing is fit to fight."""
        return self.unconscious_count == 0 and self.fleeing_count == 0


@dataclass(frozen=True, kw_only=True)
class MonthStanding:
    """
    What the player still has open before the month turns, and what shape his war band is in.

    A thing earns a place here if it *expires when the month turns* - the board is redrawn, the shop
    and the pub are restocked, a building may be raised once, a rival is open to be marched on for
    as long as his men are free - or if it *blocks the month*, which only an unresolved skirmish
    does. That rule is what keeps the page from becoming a second navbar with numbers on it, and it
    is why the fyrd reserve and the captives sit on [WarbandStanding] instead.

    Every count is asked through the queryset the acting view resolves with, for the reason the
    attack button already does: a dashboard offering a fight the attack view then refuses is worse
    than a dashboard offering nothing.

    The purse is deliberately absent. It is the same "wage_bill_payroll" the salary run bills from
    and the navbar warns from, put on every render by the finance context processor, and the cost
    card reads it from there - a copy assembled here could name a different man than the month takes.
    """

    open_skirmish_count: int
    quest_count: int
    # Named rather than counted, because "which rival" is a fact about the player's own war band and
    # a player who has to click to find out has learned nothing. Nothing about their strength: that
    # is knowledge scouting is for.
    attackable_rival_list: list
    occupiable_rival_list: list
    can_build: bool
    shop_item_count: int
    pub_mercenary_count: int
    building_income: int
    warband: WarbandStanding

    @property
    def has_anything_open(self) -> bool:
        """
        Whether anything at all is left to do before the month may be pressed.

        Read to tell "here is what is still open" from "the month is ready", which is a different
        sentence and not an empty panel.
        """
        return bool(
            self.open_skirmish_count
            or self.quest_count
            or self.attackable_rival_list
            or self.occupiable_rival_list
            or self.can_build
            or self.shop_item_count
            or self.pub_mercenary_count
        )

    @classmethod
    def for_savegame(cls, *, savegame) -> MonthStanding | None:
        """
        The one place that touches the database, the way "Payroll.for_faction" is for the wage bill.

        None where the savegame has no player faction yet - a reachable state, since the savegame row
        is created before the faction is - so the page asks one question instead of guarding every
        panel separately.
        """
        player_faction = savegame.player_faction
        if player_faction is None:
            return None

        month = savegame.current_month

        # A town is created together with its faction, so this is a guard rather than a state the
        # player reaches. Without it a savegame half-way through its creation answers 500 on the
        # first page it lands on.
        town = Town.objects.filter(faction_id=player_faction.id).first()

        return cls(
            open_skirmish_count=Skirmish.objects.for_savegame(savegame_id=savegame.id).unresolved().count(),
            quest_count=Quest.objects.for_player_faction(faction_id=player_faction.id).resolvable(month=month).count(),
            attackable_rival_list=list(Faction.objects.attackable_by(savegame=savegame).order_by("name")),
            occupiable_rival_list=list(Faction.objects.occupiable_by(savegame=savegame).order_by("name")),
            can_build=town is not None and town.last_constructed_building_at != month,
            shop_item_count=player_faction.available_items.count(),
            pub_mercenary_count=player_faction.available_mercenaries.count(),
            # Read off the town the way the month reads it, rather than assembled from a building
            # here. The cost card promises this figure and the month pays it, and the two must agree.
            building_income=town.get_monthly_income() if town else 0,
            warband=_build_warband_standing(player_faction=player_faction, month=month),
        )


def _build_warband_standing(*, player_faction, month: int) -> WarbandStanding:
    condition_counts = (
        Warrior.objects.for_player_faction(faction_id=player_faction.id)
        .exclude_dead()
        .aggregate(
            warrior_count=Count("id"),
            unconscious_count=Count("id", filter=Q(condition=Warrior.ConditionChoices.CONDITION_UNCONSCIOUS)),
            fleeing_count=Count("id", filter=Q(condition=Warrior.ConditionChoices.CONDITION_FLEEING)),
        )
    )

    return WarbandStanding(
        leader=player_faction.leader,
        leader_can_march=player_faction.get_available_leader(month=month) is not None,
        fyrd_reserve=player_faction.fyrd_reserve,
        captive_count=player_faction.captured_warriors.count(),
        **condition_counts,
    )
