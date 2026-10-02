from apps.warband.skirmish.models.warrior import Warrior
from apps.warband.skirmish.projections.payroll import Payroll
from apps.warband.templatetags.purse import net_of_wages, signed


def _payroll_of(*, wages: int) -> Payroll:
    return Payroll(warrior_list=[Warrior(monthly_salary=wages)], budget=1000)


def test_net_of_wages_of_a_month_that_makes_silver():
    result = net_of_wages(50, _payroll_of(wages=30))

    assert result == "+20"


def test_net_of_wages_of_a_month_that_loses_silver():
    result = net_of_wages(20, _payroll_of(wages=50))

    assert result == "\N{MINUS SIGN}30"


def test_net_of_wages_of_a_month_that_breaks_even():
    result = net_of_wages(30, _payroll_of(wages=30))

    assert result == "±0"


def test_signed_of_a_gain():
    result = signed(5)

    assert result == "+5"


def test_signed_of_a_loss_takes_a_true_minus_sign():
    result = signed(-60)

    assert result == "\N{MINUS SIGN}60"


def test_signed_of_nothing():
    result = signed(0)

    assert result == "±0"
