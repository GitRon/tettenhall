from dataclasses import dataclass

from django.db.models import Count

from apps.warband.skirmish.choices.posting import POSTINGS_IN_DISPLAY_ORDER, PostingChoices
from apps.warband.skirmish.models.warrior import Warrior
from apps.warband.skirmish.raids import RAID_KINDS
from apps.warband.skirmish.raids.base import RaidKind
from apps.warband.warrior.services.availability import WarriorAvailability, assess_roster

# Each place is where one raid kind lands, so the people who turn out there are that kind's
RAID_KIND_BY_POSTING: dict[int, type[RaidKind]] = {raid_kind.POSTING: raid_kind for raid_kind in RAID_KINDS}


@dataclass(frozen=True, kw_only=True)
class PlaceStanding:
    """
    One of a war band's places, and how many of its men a raid landing there today would meet.

    Who stands where is public, for every faction - see docs/patterns/warrior-knowledge.md - so this is
    the summary a rival's page shows of the rival, and the Month page of the player.
    """

    posting: int
    label: str
    # Fit, and not away on a quest or in a fight this month: the men "get_raid_defenders" would muster
    standing_count: int


def count_men_standing(*, faction_id: int, month: int) -> list[PlaceStanding]:
    """
    How many men stand at each of a faction's places today, in display order, out of one aggregate.

    Counted the way a raid musters: a man who is down, away on a quest or already in a fight is posted
    somewhere and is not there to stand in anybody's way.
    """
    counts = dict(
        Warrior.objects.filter_faction(faction_id=faction_id)
        .filter_healthy()
        .exclude_currently_busy(month=month)
        .values_list("posting")
        .annotate(standing_count=Count("id"))
        .order_by()
    )

    return [
        PlaceStanding(posting=posting, label=PostingChoices(posting).label, standing_count=counts.get(posting, 0))
        for posting in POSTINGS_IN_DISPLAY_ORDER
    ]


@dataclass(frozen=True, kw_only=True)
class PostingColumn:
    """
    One place on the player's postings page: who is posted there, and what a raid on it meets besides.

    Every living man of the war band is in exactly one column, the ones a raid would not find there
    today included, each greyed with the reason [assess_roster] gives - see
    docs/patterns/warrior-availability.md. He keeps his posting while he is away or down, so that is
    where he is drawn.
    """

    posting: int
    label: str
    raid_kind: type[RaidKind]
    men: list[WarriorAvailability]

    @property
    def standing_count(self) -> int:
        return sum(1 for man in self.men if man.is_available)

    @property
    def other_postings(self) -> list[tuple[int, str]]:
        """The places a man here can be sent to instead, as the value his move posts and its name."""
        return [
            (posting, PostingChoices(posting).label) for posting in POSTINGS_IN_DISPLAY_ORDER if posting != self.posting
        ]


def get_posting_columns(*, faction_id: int, month: int) -> list[PostingColumn]:
    """
    The player's war band laid out by where each man stands, a column per place in display order.

    One roster assessment for the whole page, so the reason a man is greyed and the count of who stands
    at his place cannot be two answers.
    """
    roster = assess_roster(faction_id=faction_id, month=month)

    return [
        PostingColumn(
            posting=posting,
            label=PostingChoices(posting).label,
            raid_kind=RAID_KIND_BY_POSTING[posting],
            men=[man for man in roster.assessed if man.warrior.posting == posting],
        )
        for posting in POSTINGS_IN_DISPLAY_ORDER
    ]
