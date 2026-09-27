from unittest import mock

from apps.warband.calendar.date import START_YEAR_EARLIEST, START_YEAR_LATEST, CalendarDate, draw_start_year
from apps.warband.calendar.months import AefterraGeola, Haligmonath


def test_draw_start_year_draws_within_the_range():
    with mock.patch("apps.warband.calendar.date.random.randint", return_value=768) as mocked_draw:
        result = draw_start_year()

    assert result == 768
    assert mocked_draw.call_args.args == (START_YEAR_EARLIEST, START_YEAR_LATEST)


def test_for_month_in_the_first_year():
    assert CalendarDate.for_month(month=6, start_year=768) == CalendarDate(calendar_month=Haligmonath, year=768)


def test_for_month_after_the_year_turns():
    assert CalendarDate.for_month(month=10, start_year=768) == CalendarDate(calendar_month=AefterraGeola, year=769)


def test_season_label():
    assert CalendarDate(calendar_month=Haligmonath, year=768).season_label == "Haligmonath · Summer"


def test_label():
    assert CalendarDate(calendar_month=AefterraGeola, year=769).label == "Æfterra Geola · Winter · AD 769"
