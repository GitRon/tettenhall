from django.urls import reverse

from apps.common.tests.html import parse, render_component
from apps.warband.skirmish.models import Warrior
from apps.warband.skirmish.projections.payroll import Payroll
from apps.warband.skirmish.tests.factories.warrior import WarriorFactory

WARNING_TAG = '<c-finance.wage-bill-warning :payroll="payroll" />'
LINKED_WARNING_TAG = '<c-finance.wage-bill-warning :payroll="payroll" show_finance_link />'


def _text(html: str) -> str:
    """
    The words as a player reads them: the template wraps its sentences across lines, and the newlines
    reach the text nodes.
    """
    return " ".join(parse(html).get_text(" ").split())


def _short_payroll(*, unpaid_months: int = 0) -> Payroll:
    return Payroll(
        warrior_list=[
            WarriorFactory.build(id=1, name="Leofric", monthly_salary=30),
            WarriorFactory.build(id=2, name="Wulfstan", monthly_salary=40, unpaid_months=unpaid_months),
        ],
        budget=0,
        leader_id=1,
    )


def test_wage_bill_warning_is_silent_while_the_wages_are_covered():
    payroll = Payroll(warrior_list=[WarriorFactory.build(id=1, monthly_salary=30)], budget=100, leader_id=1)

    html = render_component(tag=LINKED_WARNING_TAG, context={"payroll": payroll})

    result = parse(html).get_text(strip=True)

    assert result == ""


def test_wage_bill_warning_names_the_shortfall_and_every_unpaid_man():
    html = render_component(tag=WARNING_TAG, context={"payroll": _short_payroll()})

    result = _text(html)

    assert "70 silver short of next month's wages" in result
    assert "Leofric (30 silver, your leader, who never walks)" in result
    assert f"Wulfstan (40 silver, 1 of {Warrior.UNPAID_MONTHS_UNTIL_WALKOUT} unpaid months)" in result


def test_wage_bill_warning_names_the_men_about_to_walk_out():
    payroll = _short_payroll(unpaid_months=Warrior.UNPAID_MONTHS_UNTIL_WALKOUT - 1)

    html = render_component(tag=WARNING_TAG, context={"payroll": payroll})

    result = _text(html)

    assert "Leaving the war band over it: Wulfstan" in result


def test_wage_bill_warning_walk_out_line_absent_while_nobody_is_at_the_end_of_his_patience():
    html = render_component(tag=WARNING_TAG, context={"payroll": _short_payroll()})

    result = _text(html)

    assert "Leaving the war band" not in result


def test_wage_bill_warning_links_the_books_when_asked_to():
    html = render_component(tag=LINKED_WARNING_TAG, context={"payroll": _short_payroll()})

    result = [link["href"] for link in parse(html).find_all("a")]

    assert result == [reverse("warband:transaction-list-view")]


def test_wage_bill_warning_has_no_link_by_default():
    html = render_component(tag=WARNING_TAG, context={"payroll": _short_payroll()})

    result = parse(html).find_all("a")

    assert result == []
