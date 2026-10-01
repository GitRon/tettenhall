from apps.common.tests.html import parse, render_component
from apps.warband.warrior.domain.knowledge import WarriorKnowledge

ATTRIBUTE_TAG = '<c-warrior.attribute :value="value" :baseline="baseline" :knowledge="knowledge" />'


def test_attribute_exact_for_a_man_he_commands():
    html = render_component(
        tag=ATTRIBUTE_TAG, context={"value": 14, "baseline": 10, "knowledge": WarriorKnowledge.COMMANDED}
    )

    result = parse(html).get_text(strip=True)

    assert result == "14"


def test_attribute_bucketed_for_a_rival():
    html = render_component(
        tag=ATTRIBUTE_TAG, context={"value": 14, "baseline": 10, "knowledge": WarriorKnowledge.RIVAL}
    )

    result = parse(html).get_text(strip=True)

    assert result == "High"
