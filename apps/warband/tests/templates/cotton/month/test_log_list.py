from django.urls import reverse

from apps.common.tests.html import parse, render_component
from apps.warband.incident.incidents.base import IncidentOption
from apps.warband.incident.services.pending_incident import OpenQuestion
from apps.warband.incident.tests.factories.pending_incident import PendingIncidentFactory
from apps.warband.month.services.player_month_log import GroupedPlayerMonthLog
from apps.warband.month.tests.factories.player_month_log import PlayerMonthLogFactory

LOG_LIST_TAG = '<c-month.log-list :logs="logs" :questions="questions" />'


def _text(html: str) -> str:
    return " ".join(parse(html).get_text(" ").split())


def _question() -> OpenQuestion:
    return OpenQuestion(
        pending_incident=PendingIncidentFactory.build(id=7, title="The abbot asks for lead", body="For the roof."),
        options=(
            IncidentOption(key="give", label="Give it", title="", body="", silver_change=-60, fyrd_change=1),
            IncidentOption(key="refuse", label="Refuse", title="", body=""),
        ),
    )


def test_log_list_says_so_when_the_month_brought_nothing():
    html = render_component(tag=LOG_LIST_TAG, context={"logs": GroupedPlayerMonthLog(), "questions": []})

    result = _text(html)

    assert result == "Nothing to report this month."


def test_log_list_without_questions_passed_still_reports_an_empty_month():
    html = render_component(tag='<c-month.log-list :logs="logs" />', context={"logs": GroupedPlayerMonthLog()})

    result = _text(html)

    assert result == "Nothing to report this month."


def test_log_list_an_open_question_is_news_enough():
    html = render_component(tag=LOG_LIST_TAG, context={"logs": GroupedPlayerMonthLog(), "questions": [_question()]})

    result = _text(html)

    assert "Nothing to report this month." not in result


def test_log_list_asks_the_question_with_its_title_and_body():
    html = render_component(tag=LOG_LIST_TAG, context={"logs": GroupedPlayerMonthLog(), "questions": [_question()]})

    result = _text(html)

    assert result.startswith("The abbot asks for lead For the roof.")


def test_log_list_offers_every_answer_posting_to_the_question():
    html = render_component(tag=LOG_LIST_TAG, context={"logs": GroupedPlayerMonthLog(), "questions": [_question()]})

    result = [(button["hx-post"], button["hx-vals"]) for button in parse(html).find_all("button")]

    answer_url = reverse("warband:pending-incident-answer-view", args=[7])
    assert result == [(answer_url, '{"option": "give"}'), (answer_url, '{"option": "refuse"}')]


def test_log_list_signs_what_an_answer_costs_and_gives():
    html = render_component(tag=LOG_LIST_TAG, context={"logs": GroupedPlayerMonthLog(), "questions": [_question()]})

    result = [" ".join(button.get_text(" ").split()) for button in parse(html).find_all("button")]

    assert result == ["Give it \N{MINUS SIGN}60 silver +1 fyrd", "Refuse"]


def test_log_list_tells_a_chronicle_entry_with_its_body():
    logs = GroupedPlayerMonthLog(chronicle=[PlayerMonthLogFactory.build(title="A comet", body="It hangs over Mercia.")])

    html = render_component(tag=LOG_LIST_TAG, context={"logs": logs, "questions": []})

    result = _text(html)

    assert result == "A comet It hangs over Mercia."


def test_log_list_tells_what_a_chronicle_entry_brought_home():
    logs = GroupedPlayerMonthLog(
        chronicle=[PlayerMonthLogFactory.build(title="The barley is in", body="", tags=["70 silver", "Weapon"])]
    )

    html = render_component(tag=LOG_LIST_TAG, context={"logs": logs, "questions": []})

    result = _text(html)

    assert result == "The barley is in 70 silver Weapon"


def test_log_list_leaves_consequences_and_upkeep_to_the_brief():
    logs = GroupedPlayerMonthLog(
        consequence=[PlayerMonthLogFactory.build(title="Wages paid")],
        upkeep=[PlayerMonthLogFactory.build(title="Wulfstan mends")],
        upkeep_summary=["1 man mends"],
    )

    html = render_component(tag=LOG_LIST_TAG, context={"logs": logs, "questions": []})

    result = _text(html)

    assert result == ""
