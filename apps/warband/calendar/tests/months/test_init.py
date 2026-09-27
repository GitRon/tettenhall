from apps.warband.calendar.months import (
    AefterraGeola,
    Eosturmonath,
    Hredmonath,
    Winterfylleth,
    get_calendar_month,
    get_years_passed,
)


def test_get_calendar_month_opens_the_game_in_spring():
    assert get_calendar_month(month=1) is Eosturmonath


def test_get_calendar_month_reaches_the_first_winter_in_month_seven():
    assert get_calendar_month(month=7) is Winterfylleth


def test_get_calendar_month_ends_the_first_game_year_in_month_twelve():
    assert get_calendar_month(month=12) is Hredmonath


def test_get_calendar_month_comes_round_again_after_twelve_months():
    assert get_calendar_month(month=13) is Eosturmonath


def test_get_years_passed_before_the_year_turns():
    assert get_years_passed(month=9) == 0


def test_get_years_passed_once_the_year_turns_with_aefterra_geola():
    """Bede's year starts after Yule, so the game's first year turns in its tenth month."""
    assert (get_calendar_month(month=10), get_years_passed(month=10)) == (AefterraGeola, 1)
