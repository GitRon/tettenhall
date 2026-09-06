from collections import Counter
from dataclasses import dataclass, field

from apps.month.models.player_month_log import PlayerMonthLog


@dataclass(kw_only=True)
class GroupedPlayerMonthLog:
    """
    One month's log, split into the three weights it is read at.

    "upkeep_summary" is what keeps the list short: the recovery sweeps write one line per warrior, so
    a war band coming out of a fought month produces more upkeep than everything else put together,
    and none of it is worth a line of its own. The rows themselves stay in "upkeep" for the reader
    who wants them.
    """

    attention: list[PlayerMonthLog] = field(default_factory=list)
    consequence: list[PlayerMonthLog] = field(default_factory=list)
    upkeep: list[PlayerMonthLog] = field(default_factory=list)
    upkeep_summary: list[str] = field(default_factory=list)

    @property
    def is_empty(self) -> bool:
        return not (self.attention or self.consequence or self.upkeep)


def group_player_month_logs(*, player_month_logs) -> GroupedPlayerMonthLog:
    """
    Group a month's log by how loudly each line should speak.

    Takes whatever the caller already has - a queryset or a list - and evaluates it once, so the
    dashboard does not pay for a second query per weight.
    """
    grouped = GroupedPlayerMonthLog()

    buckets = {
        PlayerMonthLog.CategoryChoices.CATEGORY_ATTENTION: grouped.attention,
        PlayerMonthLog.CategoryChoices.CATEGORY_CONSEQUENCE: grouped.consequence,
        PlayerMonthLog.CategoryChoices.CATEGORY_UPKEEP: grouped.upkeep,
    }

    for player_month_log in player_month_logs:
        buckets[player_month_log.category].append(player_month_log)

    grouped.upkeep_summary = _summarise_upkeep(player_month_logs=grouped.upkeep)

    return grouped


def _summarise_upkeep(*, player_month_logs: list[PlayerMonthLog]) -> list[str]:
    # Counted in the order the kinds first appear rather than sorted, so the sentence reads in the
    # order the month happened - Counter preserves insertion order
    counts = Counter(player_month_log.kind for player_month_log in player_month_logs)

    return [_upkeep_phrase(kind=kind, count=count) for kind, count in counts.items()]


def _upkeep_phrase(*, kind: int, count: int) -> str:
    singular, plural = PlayerMonthLog.UPKEEP_SUMMARY_PHRASES[kind]

    return f"{count} {singular if count == 1 else plural}"
