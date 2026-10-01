from apps.common.tests.html import parse, render_component
from apps.warband.month.services.player_month_log import GroupedPlayerMonthLog
from apps.warband.month.tests.factories.player_month_log import PlayerMonthLogFactory

LOG_BRIEF_TAG = '<c-month.log-brief :logs="logs" />'


def _text(html: str) -> str:
    return " ".join(parse(html).get_text(" ").split())


def test_log_brief_is_silent_without_consequences_or_upkeep():
    logs = GroupedPlayerMonthLog(
        attention=[PlayerMonthLogFactory.build(title="Unpaid")],
        chronicle=[PlayerMonthLogFactory.build(title="A comet", body="It hangs over Mercia.")],
    )

    html = render_component(tag=LOG_BRIEF_TAG, context={"logs": logs})

    result = _text(html)

    assert result == ""


def test_log_brief_lists_every_consequence():
    logs = GroupedPlayerMonthLog(
        consequence=[PlayerMonthLogFactory.build(title="Wages paid"), PlayerMonthLogFactory.build(title="Hall raised")],
    )

    html = render_component(tag=LOG_BRIEF_TAG, context={"logs": logs})

    result = _text(html)

    assert result == "The month's work Wages paid Hall raised"


def test_log_brief_tallies_the_upkeep_into_its_summary():
    logs = GroupedPlayerMonthLog(
        upkeep=[PlayerMonthLogFactory.build(title="Wulfstan mends")],
        upkeep_summary=["1 man mends"],
    )

    html = render_component(tag=LOG_BRIEF_TAG, context={"logs": logs})

    result = parse(html).find("summary").get_text(strip=True)

    assert result == "1 man mends"
