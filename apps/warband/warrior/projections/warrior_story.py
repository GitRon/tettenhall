from dataclasses import dataclass

from apps.warband.calendar.date import CalendarDate
from apps.warband.quest.models.quest_contract import QuestContract
from apps.warband.skirmish.models import Skirmish, SkirmishCasualty, SkirmishWarriorGrowth, Warrior
from apps.warband.warrior.choices.nickname import NicknameStateChoices
from apps.warband.warrior.choices.warrior_milestone import JoinedWayChoices, MilestoneKindChoices
from apps.warband.warrior.models.injury import Injury
from apps.warband.warrior.models.warrior_milestone import WarriorMilestone
from apps.warband.warrior.services.nickname import resolve_nickname

# How many entries his page tells, newest first. A veteran's history only grows - a fight a month, and
# every blow of it on a row - so the page reads the latest of each source rather than all of it
STORY_LENGTH = 12

# A fight can bring several milestones at once - a name and a change in him - so the milestones are read
# further back than the entries, so the fights on the page still carry what they brought
MILESTONES_READ = STORY_LENGTH * 3

# Within one month, the order things happen in: a man joins before he is sent anywhere, is sent before
# he fights, and is marked by the fight he fought
_RANK_JOINED = 0
_RANK_ERRAND = 1
_RANK_FIGHT = 2
_RANK_INJURY = 3
_RANK_MILESTONE = 4

_JOINED_WORDING = {
    JoinedWayChoices.FOUNDED: "Led {faction} from its first day",
    JoinedWayChoices.DRAFTED: "Drafted from the fyrd of {faction}",
    JoinedWayChoices.HIRED: "Hired from the pub by {faction}",
    JoinedWayChoices.SWORN_FROM_CELLS: "Sworn in from the cells of {faction}",
    JoinedWayChoices.ERRAND_REWARD: "Came to {faction} as an errand's reward",
    JoinedWayChoices.RAISED_TO_LEAD: "Raised by the fyrd of {faction} to lead it",
}

# Why a deed epithet was earned. An attribute epithet has no reason to give: it names how he stands,
# not something he did
_DEED_REASONS = {
    NicknameStateChoices.RELIC_BEARER: "for carrying the hall's relic",
    NicknameStateChoices.WALLBREAKER: "for the swing that brought the walls down",
    NicknameStateChoices.UNBROKEN: "for being the last man standing",
    NicknameStateChoices.OLD_WOLF: "for all the fights he came home from",
}

CHANGED_WORDING = "Came back from the fight a different man"


@dataclass(frozen=True, kw_only=True)
class StoryEntry:
    """
    One thing that happened to him, as his page tells it: when, what, and the lines that belong to it.
    """

    when: CalendarDate
    headline: str
    details: tuple[str, ...] = ()
    # Month, then the order things happen in within a month, then the order the rows were written in
    order: tuple[int, int, int]


@dataclass(frozen=True, kw_only=True)
class WarriorStory:
    """
    What a man has done, newest first: how he came to the war band, the fights he stood in and how each
    ended for him, the men he killed, the levels he reached, the names he earned and why, his errands
    and his wounds.

    Read mostly off what the game already records as it happens - the fights, their casualties and what
    each gave him, the errands and the injuries - and for the moments nothing else keeps, off his
    "WarriorMilestone" rows.

    Public, the way his epithet is, with one exception: a change a fight made in him is told only where
    the viewer saw it, which is under the viewer's own banner - see docs/patterns/warrior-knowledge.md.
    Nothing here carries a number the knowledge rule fuzzes: no blow, no damage, no attribute.
    """

    entries: list[StoryEntry]

    @classmethod
    def for_warrior(cls, *, warrior: Warrior, viewer_faction_id: int | None) -> WarriorStory:
        start_year = warrior.savegame.start_year
        attacked_in = set(Skirmish.objects.resolved().filter(attacking_warriors=warrior).values_list("id", flat=True))
        defended_in = set(Skirmish.objects.resolved().filter(defending_warriors=warrior).values_list("id", flat=True))
        fight_ids = sorted(attacked_in | defended_in, reverse=True)[:STORY_LENGTH]

        milestone_lines, entries = _milestone_entries(
            warrior=warrior, fight_ids=fight_ids, viewer_faction_id=viewer_faction_id, start_year=start_year
        )
        entries += _fight_entries(
            warrior=warrior,
            fight_ids=fight_ids,
            attacked_in=attacked_in,
            milestone_lines=milestone_lines,
            start_year=start_year,
        )
        entries += _errand_entries(warrior=warrior, start_year=start_year)
        entries += _injury_entries(warrior=warrior, start_year=start_year)

        entries.sort(key=lambda entry: entry.order, reverse=True)

        return cls(entries=entries[:STORY_LENGTH])


def _date(*, month: int, start_year: int) -> CalendarDate:
    return CalendarDate.for_month(month=month, start_year=start_year)


def _milestone_entries(
    *, warrior: Warrior, fight_ids: list[int], viewer_faction_id: int | None, start_year: int
) -> tuple[dict[int, list[str]], list[StoryEntry]]:
    """
    His milestones, newest first: the lines that belong under a fight the page tells, by the fight, and
    an entry of its own for every other one. A change the viewer did not see is left out.
    """
    milestone_lines: dict[int, list[str]] = {}
    entries: list[StoryEntry] = []
    for milestone in (
        WarriorMilestone.objects.for_warrior(warrior_id=warrior.id)
        .select_related("faction", "other_warrior")
        .order_by("-id")[:MILESTONES_READ]
    ):
        if milestone.kind == MilestoneKindChoices.CHANGED and not _was_seen(
            milestone=milestone, viewer_faction_id=viewer_faction_id
        ):
            continue

        line = describe_milestone(milestone=milestone, nickname_variant=warrior.nickname_variant)
        if milestone.skirmish_id in fight_ids:
            milestone_lines.setdefault(milestone.skirmish_id, []).append(line)
            continue

        rank = (
            _RANK_JOINED
            if milestone.kind in {MilestoneKindChoices.JOINED, MilestoneKindChoices.TOOK_SEAT}
            else _RANK_MILESTONE
        )
        entries.append(
            StoryEntry(
                when=_date(month=milestone.month, start_year=start_year),
                headline=line,
                order=(milestone.month, rank, milestone.id),
            )
        )

    return milestone_lines, entries


def _fight_entries(
    *,
    warrior: Warrior,
    fight_ids: list[int],
    attacked_in: set[int],
    milestone_lines: dict[int, list[str]],
    start_year: int,
) -> list[StoryEntry]:
    """
    One entry per decided fight he stood in: for whom, against whom and how it went, and under it how it
    ended for him, whom he killed, the level it brought him and the milestones it brought.
    """
    fates = {
        casualty.skirmish_id: casualty.get_fate_display()
        for casualty in SkirmishCasualty.objects.filter(skirmish_id__in=fight_ids, warrior=warrior)
    }
    killed: dict[int, list[str]] = {}
    for casualty in (
        SkirmishCasualty.objects.filter(skirmish_id__in=fight_ids, killed_by=warrior)
        .select_related("warrior")
        .order_by("id")
    ):
        killed.setdefault(casualty.skirmish_id, []).append(casualty.warrior.name)
    reached_levels = {
        skirmish_id: f"Reached level {level}"
        for skirmish_id, level in SkirmishWarriorGrowth.objects.filter(
            skirmish_id__in=fight_ids, warrior=warrior, reached_level__isnull=False
        ).values_list("skirmish_id", "reached_level")
    }

    entries = []
    for fight in Skirmish.objects.filter(id__in=fight_ids).select_related("attacking_faction", "defending_faction"):
        fought_for, fought_against = (
            (fight.attacking_faction, fight.defending_faction)
            if fight.id in attacked_in
            else (fight.defending_faction, fight.attacking_faction)
        )
        details = [
            fates.get(fight.id),
            # "Killed A and B" rather than a line per man
            f"Killed {join_names(names=killed[fight.id])}" if fight.id in killed else None,
            reached_levels.get(fight.id),
            # Oldest first under the fight, the way they happened in it
            *reversed(milestone_lines.get(fight.id, [])),
        ]
        outcome = "won" if fight.victorious_faction_id == fought_for.id else "lost"
        entries.append(
            StoryEntry(
                when=_date(month=fight.month, start_year=start_year),
                headline=f"Fought for {fought_for} against {fought_against}, and {outcome}",
                details=tuple(detail for detail in details if detail),
                order=(fight.month, _RANK_FIGHT, fight.id),
            )
        )

    return entries


def _errand_entries(*, warrior: Warrior, start_year: int) -> list[StoryEntry]:
    """The errands he was sent on, and when he came home from the ones he has."""
    return [
        StoryEntry(
            when=_date(month=contract.accepted_in_month, start_year=start_year),
            headline=f"Sent on an errand: {contract.title}",
            details=(
                (f"Came home {_date(month=contract.resolved_in_month, start_year=start_year).label}",)
                if contract.resolved_in_month
                else ()
            ),
            order=(contract.accepted_in_month, _RANK_ERRAND, contract.id),
        )
        for contract in QuestContract.objects.filter(assigned_warriors=warrior).order_by("-id")[:STORY_LENGTH]
    ]


def _injury_entries(*, warrior: Warrior, start_year: int) -> list[StoryEntry]:
    """The lasting marks he took, in the month he took each."""
    return [
        StoryEntry(
            when=_date(month=injury.inflicted_in_month, start_year=start_year),
            headline=f"Marked for good: {injury.type.description}",
            order=(injury.inflicted_in_month, _RANK_INJURY, injury.id),
        )
        for injury in Injury.objects.for_warrior(warrior_id=warrior.id)
        .select_related("type")
        .order_by("-id")[:STORY_LENGTH]
    ]


def _was_seen(*, milestone: WarriorMilestone, viewer_faction_id: int | None) -> bool:
    """
    Whether the viewer watched this happen: it did if the man stood under the viewer's banner then.
    """
    return milestone.faction_id is not None and milestone.faction_id == viewer_faction_id


def describe_milestone(*, milestone: WarriorMilestone, nickname_variant: int) -> str:
    """
    One milestone as a line of his story.

    The epithet is phrased by his own variant, the way the one on his card is, so the line and the card
    name him alike.
    """
    if milestone.kind == MilestoneKindChoices.JOINED:
        return _JOINED_WORDING[milestone.joined_way].format(faction=milestone.faction)

    if milestone.kind == MilestoneKindChoices.TOOK_SEAT:
        if milestone.other_warrior is None:
            return f"Took the seat at the head of {milestone.faction}"
        return f"Took the seat of {milestone.other_warrior.name} at the head of {milestone.faction}"

    if milestone.kind == MilestoneKindChoices.NAMED:
        name = resolve_nickname(state=milestone.nickname_state, variant=nickname_variant)
        reason = describe_naming_reason(nickname_state=milestone.nickname_state, other_warrior=milestone.other_warrior)
        return f"Came to be called {name} {reason}" if reason else f"Came to be called {name}"

    return CHANGED_WORDING


def describe_naming_reason(*, nickname_state: int, other_warrior: Warrior | None) -> str | None:
    """
    Why he was named, for a deed; None for an epithet that names how he stands rather than what he did.

    The two deeds done to another man name him, when the record still has him.
    """
    if nickname_state == NicknameStateChoices.LORD_SLAYER:
        return f"for the blow that killed {other_warrior.name}" if other_warrior else "for the blow that killed a lord"

    if nickname_state == NicknameStateChoices.GIANTBANE:
        return (
            f"for felling {other_warrior.name}, a man far above him"
            if other_warrior
            else "for felling a man far above him"
        )

    return _DEED_REASONS.get(nickname_state)


def join_names(*, names: list[str]) -> str:
    """The names in a sentence: "A", "A and B", "A, B and C"."""
    if len(names) == 1:
        return names[0]

    return f"{', '.join(names[:-1])} and {names[-1]}"
