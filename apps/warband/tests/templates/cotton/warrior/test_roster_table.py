from apps.common.tests.html import parse, render_component


def _footer_text(html: str) -> str | None:
    footer = parse(html).find("tfoot")

    return " ".join(footer.get_text(" ").split()) if footer else None


def test_roster_table_sums_the_wage_bill_under_the_wage_column():
    html = render_component(tag='<c-warrior.roster-table :wage_total="wage_total" />', context={"wage_total": 120})

    result = _footer_text(html)

    assert result == "Wage bill / month 120"


def test_roster_table_without_a_wage_bill_draws_no_total():
    """
    The cells pass none: a prisoner's wage is what recruiting him would cost, and a sum of men nobody
    has taken on is not a bill.
    """
    html = render_component(tag="<c-warrior.roster-table />", context={})

    result = _footer_text(html)

    assert result is None


def test_roster_table_is_named_for_assistive_technology():
    html = render_component(tag='<c-warrior.roster-table label="Prisoners" />', context={})

    result = parse(html).find("table")["aria-label"]

    assert result == "Prisoners"
