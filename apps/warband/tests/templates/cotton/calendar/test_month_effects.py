from apps.common.tests.html import parse, render_component
from apps.warband.calendar.months.summer import Eosturmonath
from apps.warband.calendar.months.winter import Blotmonath

MONTH_EFFECTS_TAG = '<c-calendar.month-effects :calendar_month="calendar_month" />'


def test_month_effects_lists_every_effect_in_force():
    html = render_component(tag=MONTH_EFFECTS_TAG, context={"calendar_month": Blotmonath})

    result = [item.get_text(strip=True) for item in parse(html).find_all("li")]

    assert result == list(Blotmonath.get_effects())


def test_month_effects_says_so_when_the_month_levers_nothing():
    html = render_component(tag=MONTH_EFFECTS_TAG, context={"calendar_month": Eosturmonath})

    result = [item.get_text(strip=True) for item in parse(html).find_all("li")]

    assert result == ["Nothing out of the ordinary."]


def test_month_effects_labels_the_month_without_a_heading():
    html = render_component(tag=MONTH_EFFECTS_TAG, context={"calendar_month": Eosturmonath})

    result = " ".join(parse(html).find("div").get_text(" ").split())

    assert result.startswith("Eosturmonath · Summer")


def test_month_effects_puts_the_heading_before_the_month():
    html = render_component(
        tag='<c-calendar.month-effects heading="Next" :calendar_month="calendar_month" />',
        context={"calendar_month": Eosturmonath},
    )

    result = " ".join(parse(html).find("div").get_text(" ").split())

    assert result.startswith("Next · Eosturmonath · Summer")
