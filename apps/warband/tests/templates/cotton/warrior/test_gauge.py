from apps.common.tests.html import parse, render_component
from apps.warband.warrior.domain.knowledge import WarriorKnowledge

GAUGE_TAG = (
    '<c-warrior.gauge :current="current" :maximum="maximum" :peak="peak" :baseline="baseline" :knowledge="knowledge" />'
)


def test_gauge_exact_for_a_man_he_commands():
    html = render_component(
        tag=GAUGE_TAG,
        context={"current": 3, "maximum": 5, "peak": None, "baseline": 4, "knowledge": WarriorKnowledge.COMMANDED},
    )

    result = parse(html).get_text(" ", strip=True)

    assert result == "3/5"


def test_gauge_exact_names_the_peak_he_was_cut_from():
    html = render_component(
        tag=GAUGE_TAG,
        context={"current": 3, "maximum": 5, "peak": 9, "baseline": 4, "knowledge": WarriorKnowledge.COMMANDED},
    )

    result = parse(html).get_text(" ", strip=True)

    assert result == "3/5 (was 9)"


def test_gauge_fuzzed_for_a_rival():
    html = render_component(
        tag=GAUGE_TAG,
        context={"current": 3, "maximum": 5, "peak": 9, "baseline": 4, "knowledge": WarriorKnowledge.RIVAL},
    )

    result = parse(html).get_text(" ", strip=True)

    assert result == "Low"
