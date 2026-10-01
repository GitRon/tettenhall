from apps.common.tests.html import parse, render_component
from apps.warband.calendar.months.summer import Eosturmonath
from apps.warband.calendar.months.winter import Blotmonath

MARCH_COST_ROW_TAG = '<c-calendar.march-cost-row :calendar_month="calendar_month" />'


def _text(html: str) -> str:
    return " ".join(parse(f"<table>{html}</table>").get_text(" ").split())


def test_march_cost_row_prices_a_winter_march_per_man():
    html = render_component(tag=MARCH_COST_ROW_TAG, context={"calendar_month": Blotmonath})

    result = _text(html)

    assert result == "March this month 5 silver per man · Blotmonath · Winter"


def test_march_cost_row_says_a_summer_march_is_free():
    html = render_component(tag=MARCH_COST_ROW_TAG, context={"calendar_month": Eosturmonath})

    result = _text(html)

    assert result == "March this month Free · Eosturmonath · Summer"
