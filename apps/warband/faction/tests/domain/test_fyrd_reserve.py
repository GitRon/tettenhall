from unittest import mock

from apps.warband.faction.domain.fyrd_reserve import FyrdReserve


def test_roll_starting_reserve_draws_between_its_bounds():
    with mock.patch("apps.warband.faction.domain.fyrd_reserve.random.randint", return_value=4) as mocked_randint:
        result = FyrdReserve.roll_starting_reserve()

    assert result == 4
    mocked_randint.assert_called_once_with(FyrdReserve.STARTING_RESERVE_MIN, FyrdReserve.STARTING_RESERVE_MAX)


def test_roll_monthly_recruits_may_send_nobody():
    with mock.patch("apps.warband.faction.domain.fyrd_reserve.random.randrange", return_value=0) as mocked_randrange:
        result = FyrdReserve.roll_monthly_recruits()

    assert result == 0
    mocked_randrange.assert_called_once_with(0, FyrdReserve.MONTHLY_RECRUITS_MAX + 1)
