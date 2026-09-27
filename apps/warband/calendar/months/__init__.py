from apps.warband.calendar.months.base import CalendarMonth
from apps.warband.calendar.months.summer import (
    AefterraLitha,
    AerraLitha,
    Eosturmonath,
    Haligmonath,
    Summer,
    Thrimilcemonath,
    Weodmonath,
)
from apps.warband.calendar.months.winter import (
    AefterraGeola,
    AerraGeola,
    Blotmonath,
    Hredmonath,
    Solmonath,
    Winter,
    Winterfylleth,
)

# Bede's twelve months in his order, which starts the year after Yule. No intercalary month: Þriliða
# is left out, so every year is twelve months long.
YEAR: tuple[type[CalendarMonth], ...] = (
    AefterraGeola,
    Solmonath,
    Hredmonath,
    Eosturmonath,
    Thrimilcemonath,
    AerraLitha,
    AefterraLitha,
    Weodmonath,
    Haligmonath,
    Winterfylleth,
    Blotmonath,
    AerraGeola,
)

# A game opens in spring, so month 1 is Eosturmonath, the first winter begins in month 7, and the year
# turns with Æfterra Geola in month 10
FIRST_MONTH = Eosturmonath


def _position_in_calendar(*, month: int) -> int:
    """How many months into Bede's calendar "month" falls, counted from the first year's Æfterra Geola."""
    return YEAR.index(FIRST_MONTH) + month - 1


def get_calendar_month(*, month: int) -> type[CalendarMonth]:
    """
    The month of the year the savegame's "month" falls in.

    Read off "current_month" alone, so every rule can ask it with the number its message already
    carries.
    """
    return YEAR[_position_in_calendar(month=month) % len(YEAR)]


def get_years_passed(*, month: int) -> int:
    """How many times the year has turned by the savegame's "month"."""
    return _position_in_calendar(month=month) // len(YEAR)
