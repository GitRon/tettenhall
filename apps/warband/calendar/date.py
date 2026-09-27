import random
from dataclasses import dataclass

from apps.warband.calendar.months import CalendarMonth, get_calendar_month, get_years_passed

# The years a savegame may open in: Mercia under Æthelbald and Offa, before the first recorded Viking
# raid on Lindisfarne in 793 - a Britain fought over by its own kingdoms. The year carries no rule, so
# where in the range a game opens cannot touch balance
START_YEAR_EARLIEST = 750
START_YEAR_LATEST = 780


def draw_start_year() -> int:
    """The year a new savegame opens in, drawn once and kept for the rest of the game."""
    return random.randint(START_YEAR_EARLIEST, START_YEAR_LATEST)


@dataclass(frozen=True, kw_only=True)
class CalendarDate:
    """
    Where in the year a savegame's month falls: the month of the year, and the year Anno Domini.

    Counted Anno Domini because Bede made that reckoning common in the same *De temporum ratione*
    the months come from.
    """

    calendar_month: type[CalendarMonth]
    year: int

    @classmethod
    def for_month(cls, *, month: int, start_year: int) -> CalendarDate:
        return cls(calendar_month=get_calendar_month(month=month), year=start_year + get_years_passed(month=month))

    @property
    def season_label(self) -> str:
        """The month and its season, which is how the month is named wherever it is shown."""
        return f"{self.calendar_month.NAME} · {self.calendar_month.SEASON}"

    @property
    def label(self) -> str:
        return f"{self.season_label} · AD {self.year}"
