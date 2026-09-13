from collections.abc import Callable, Iterable
from dataclasses import dataclass

from django.db.models import QuerySet

from apps.warband.skirmish.managers.warrior import WarriorQuerySet
from apps.warband.skirmish.models.warrior import Warrior


@dataclass(frozen=True, kw_only=True)
class WarriorAvailability:
    """
    One man on the roster, and whether he can be sent anywhere this month.

    The reason is the whole point. A picker that simply leaves a man out shows the player a shorter
    war band than the one he owns and leaves him to work out the difference himself, which is the
    most expensive way for a rule to be communicated.
    """

    warrior: Warrior
    #: Why he cannot go, in the player's words. None means he can.
    reason: str | None

    @property
    def is_available(self) -> bool:
        return self.reason is None


@dataclass(frozen=True, kw_only=True)
class _BlockingRule:
    """
    One reason a man is out, paired with the query that finds everyone it catches.

    The pairing is the design. The rules used to be performed by a queryset and explained by three
    sentences on a form, and two of the four were explained nowhere at all - so a screen could say
    one thing while the database did another. Here the sentence and the query are one row, and a
    fifth rule is one more row rather than an edit in two places.
    """

    select: Callable[[WarriorQuerySet], WarriorQuerySet]
    #: Taken per warrior rather than as a flat string, because a condition already words itself.
    reason: Callable[[Warrior], str]


REASON_SWORN_TO_A_QUEST = "Already sworn to a quest this month"
REASON_COMMITTED_TO_A_FIGHT = "Committed to a fight this month"
REASON_STANDING_IN_AN_OPEN_FIGHT = "Still standing in a fight nobody has settled"


def _blocking_rules(*, month: int) -> tuple[_BlockingRule, ...]:
    """
    The four rules, in the order a man is measured against them. First match wins.

    Unfit comes first because a dead man on a quest roster is dead before he is spoken for, and
    because his condition is the only one of the four the player can already see elsewhere.

    The two fight rules are ordered the opposite way from how they read. "This month" is the specific
    case, so putting it first leaves the open-fight sentence to fire only for a fight from some
    *other* month - which is the one exclusion in this game a player cannot guess at, and the reason
    the issue behind this was written.
    """
    return (
        _BlockingRule(
            select=lambda roster: roster.filter_unfit(),
            # Off the field's own choices rather than worded a second time here
            reason=lambda warrior: warrior.get_condition_display(),
        ),
        _BlockingRule(
            select=lambda roster: roster.filter_sworn_to_a_quest(month=month),
            reason=lambda warrior: REASON_SWORN_TO_A_QUEST,
        ),
        _BlockingRule(
            select=lambda roster: roster.filter_committed_to_a_fight(month=month),
            reason=lambda warrior: REASON_COMMITTED_TO_A_FIGHT,
        ),
        _BlockingRule(
            select=lambda roster: roster.filter_standing_in_an_open_fight(),
            reason=lambda warrior: REASON_STANDING_IN_AN_OPEN_FIGHT,
        ),
    )


@dataclass(frozen=True, kw_only=True)
class RosterAssessment:
    """
    A whole war band measured against this month, and everything a picker needs to draw it.

    One object rather than several returns, because a form that asked for the rows and the verdicts
    separately could render one and validate against the other. The three properties below are the
    same list read three ways.
    """

    #: Every man, in the order the picker draws him.
    assessed: tuple[WarriorAvailability, ...]

    @property
    def is_empty(self) -> bool:
        """
        Whether there is nobody to draw at all, which is a different page from one full of reasons.
        """
        return not self.assessed

    @property
    def has_nobody_available(self) -> bool:
        return not any(assessment.is_available for assessment in self.assessed)

    @property
    def reasons_by_warrior_id(self) -> dict[int, str]:
        """
        What the picker greys each row out with.
        """
        return {a.warrior.id: a.reason for a in self.assessed if a.reason is not None}

    @property
    def available_ids(self) -> set[int]:
        """
        What a posted value is validated against.

        The field's queryset cannot do that job any more: it has to hold the whole roster, because an
        option missing from it is an option that does not render - and drawing the men who cannot go
        is the point. So the queryset scopes to the faction and this decides who may be picked.
        """
        return {a.warrior.id for a in self.assessed if a.is_available}

    def as_queryset(self) -> QuerySet[Warrior]:
        """
        The same men as a queryset, which is what a "ModelMultipleChoiceField" takes.

        Ordered the same way the list is, so the rows the player reads and the options the field
        holds are in one order.
        """
        return Warrior.objects.filter(id__in=[a.warrior.id for a in self.assessed]).order_by("name", "id")


def assess_roster(*, faction_id: int, month: int, excluded_ids: Iterable[int] = ()) -> RosterAssessment:
    """
    The whole war band, each man carrying either a verdict or nothing.

    The whole of it, and not the part that can go: a roster the player can count against the one he
    owns is the only version of this screen that cannot be mistaken for a broken page.

    One query per rule rather than one per man. Four queries answer a roster of forty as cheaply as a
    roster of four, where asking each man in turn puts a query on every row of the page.

    "excluded_ids" is for a man who is not a choice at all, rather than one who is unavailable - the
    leader on the attack form, who marches whether or not the player ticks anything. He is left out
    of the list entirely instead of shown greyed, because "he is coming regardless" is not a reason
    he cannot go.

    Ordered by name, with the id behind it so that two men of one name hold still between requests.
    Deliberately not ordered by availability: sorting the unavailable to the bottom would undo the
    one thing drawing them achieves, which is that the list reads as the war band.
    """
    roster = Warrior.objects.filter_faction(faction_id=faction_id).exclude(id__in=excluded_ids).order_by("name", "id")

    caught = [(rule, set(rule.select(roster).values_list("id", flat=True))) for rule in _blocking_rules(month=month)]

    return RosterAssessment(
        assessed=tuple(
            WarriorAvailability(
                warrior=warrior,
                reason=next((rule.reason(warrior) for rule, ids in caught if warrior.id in ids), None),
            )
            for warrior in roster
        )
    )
