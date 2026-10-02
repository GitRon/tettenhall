from apps.common.tests.html import parse, render_component
from apps.warband.warrior.domain.knowledge import WarriorKnowledge

ROSTER_GAUGE_TAG = (
    '<c-warrior.roster-gauge :current="current" :maximum="maximum" :baseline="baseline" :knowledge="knowledge" />'
)


def test_roster_gauge_draws_the_bar_beside_exact_figures():
    html = render_component(
        tag=ROSTER_GAUGE_TAG,
        context={"current": 3, "maximum": 5, "baseline": 4, "knowledge": WarriorKnowledge.COMMANDED},
    )

    soup = parse(html)
    result = (soup.find(attrs={"aria-hidden": "true"}) is not None, soup.get_text(" ", strip=True))

    assert result == (True, "3/5")


def test_roster_gauge_held_man_gets_the_word_and_no_bar():
    html = render_component(
        tag=ROSTER_GAUGE_TAG,
        context={"current": 3, "maximum": 5, "baseline": 4, "knowledge": WarriorKnowledge.HELD},
    )

    soup = parse(html)
    result = (soup.find(attrs={"aria-hidden": "true"}) is not None, soup.get_text(" ", strip=True))

    assert result == (False, "Low")
