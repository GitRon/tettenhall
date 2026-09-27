from apps.warband.calendar.date import CalendarDate
from apps.warband.calendar.months import YEAR, AefterraGeola, AerraGeola
from apps.warband.calendar.projections.year import YearAtAGlance


def test_for_month_names_the_month_in_hand_the_next_one_and_the_whole_year():
    """The next month is dated too, so the month before the year turns looks ahead into the new year."""
    result = YearAtAGlance.for_month(month=9, start_year=768)

    assert result == YearAtAGlance(
        current=CalendarDate(calendar_month=AerraGeola, year=768),
        next=CalendarDate(calendar_month=AefterraGeola, year=769),
        months=YEAR,
    )
