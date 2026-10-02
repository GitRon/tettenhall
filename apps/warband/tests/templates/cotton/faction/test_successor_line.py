from apps.common.tests.html import parse, render_component
from apps.warband.skirmish.models import Warrior
from apps.warband.skirmish.tests.factories.warrior import WarriorFactory

SUCCESSOR_LINE_TAG = '<c-faction.successor-line :leader="leader" :successor="successor" />'


def _warrior(*, name: str) -> Warrior:
    return WarriorFactory.build(name=name, nickname_state=None)


def _text(html: str) -> str:
    return " ".join(parse(html).get_text(" ").split())


def test_successor_line_names_who_leads_next():
    html = render_component(
        tag=SUCCESSOR_LINE_TAG, context={"leader": _warrior(name="Uthred"), "successor": _warrior(name="Wulf")}
    )

    result = _text(html)

    assert result == "Should Uthred fall, Wulf leads."


def test_successor_line_without_a_successor_ends_the_war_band():
    html = render_component(tag=SUCCESSOR_LINE_TAG, context={"leader": _warrior(name="Uthred"), "successor": None})

    result = _text(html)

    assert result == "Should Uthred fall, the war band is finished."


def test_successor_line_says_nothing_without_a_leader():
    html = render_component(tag=SUCCESSOR_LINE_TAG, context={"leader": None, "successor": None})

    result = _text(html)

    assert result == ""
