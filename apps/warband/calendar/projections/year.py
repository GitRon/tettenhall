from dataclasses import dataclass

from apps.warband.calendar.date import CalendarDate
from apps.warband.calendar.months import YEAR, CalendarMonth


@dataclass(frozen=True, kw_only=True)
class YearAtAGlance:
    """
    The whole year as the dashboard lays it out: where the savegame stands, what comes next, and the
    twelve months in Bede's order.

    Read off the same month classes the rules take their numbers from, so a month's effects on the
    page are the effects it has.
    """

    current: CalendarDate
    next: CalendarDate
    months: tuple[type[CalendarMonth], ...]

    @classmethod
    def for_month(cls, *, month: int, start_year: int) -> YearAtAGlance:
        return cls(
            current=CalendarDate.for_month(month=month, start_year=start_year),
            next=CalendarDate.for_month(month=month + 1, start_year=start_year),
            months=YEAR,
        )
