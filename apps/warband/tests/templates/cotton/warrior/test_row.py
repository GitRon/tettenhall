from django.urls import reverse

from apps.common.tests.html import parse, render_component
from apps.warband.skirmish.models import Warrior
from apps.warband.skirmish.tests.factories.warrior import WarriorFactory
from apps.warband.warrior.domain.knowledge import WarriorKnowledge

ROW_TAG = '<c-warrior.row :warrior="warrior" :knowledge="knowledge" />'
PUB_ROW_TAG = (
    '<c-warrior.row :warrior="warrior" :knowledge="knowledge" is_pub :is_player_faction="is_player_faction" />'
)


def _warrior(**kwargs) -> Warrior:
    return WarriorFactory.build(id=12, name="Wulfstan", **kwargs)


def _text(html: str) -> str:
    return " ".join(parse(html).get_text(" ").split())


def test_row_leads_to_his_own_page():
    html = render_component(tag=ROW_TAG, context={"warrior": _warrior(), "knowledge": WarriorKnowledge.RIVAL})

    result = parse(html).find("a")["href"]

    assert result == reverse("warband:warrior-detail-view", args=[12])


def test_row_shows_the_gear_when_it_may_be_known():
    html = render_component(tag=ROW_TAG, context={"warrior": _warrior(), "knowledge": WarriorKnowledge.COMMANDED})

    result = _text(html)

    assert "Weapon empty-handed" in result


def test_row_hides_a_rivals_gear():
    html = render_component(tag=ROW_TAG, context={"warrior": _warrior(), "knowledge": WarriorKnowledge.RIVAL})

    result = _text(html)

    assert "Weapon" not in result


def test_row_names_the_condition_of_a_man_who_cannot_fight():
    warrior = _warrior(condition=Warrior.ConditionChoices.CONDITION_UNCONSCIOUS)

    html = render_component(tag=ROW_TAG, context={"warrior": warrior, "knowledge": WarriorKnowledge.RIVAL})

    result = _text(html)

    assert "Unconscious" in result


def test_row_says_nothing_of_a_man_who_can_fight():
    html = render_component(tag=ROW_TAG, context={"warrior": _warrior(), "knowledge": WarriorKnowledge.RIVAL})

    result = _text(html)

    assert "Healthy" not in result


def test_row_offers_the_recruit_in_the_players_own_pub():
    warrior = _warrior()

    html = render_component(
        tag=PUB_ROW_TAG, context={"warrior": warrior, "knowledge": WarriorKnowledge.RIVAL, "is_player_faction": True}
    )

    result = parse(html).find("button")["hx-post"]

    assert result == reverse("warband:pub-mercenary-recruit-view", args=[12])


def test_row_offers_no_recruit_in_a_rivals_pub():
    html = render_component(
        tag=PUB_ROW_TAG,
        context={"warrior": _warrior(), "knowledge": WarriorKnowledge.RIVAL, "is_player_faction": False},
    )

    result = parse(html).find("button")

    assert result is None


def test_row_offers_no_recruit_outside_a_pub():
    html = render_component(tag=ROW_TAG, context={"warrior": _warrior(), "knowledge": WarriorKnowledge.RIVAL})

    result = parse(html).find("button")

    assert result is None


def test_row_explains_the_back_wages_on_a_long_wait():
    warrior = _warrior(pub_arrival_month=1, monthly_salary=20)
    warrior.savegame.current_month = 24

    html = render_component(
        tag=PUB_ROW_TAG, context={"warrior": warrior, "knowledge": WarriorKnowledge.RIVAL, "is_player_faction": True}
    )

    result = _text(html)

    assert warrior.idle_surcharge > 0
    assert f"23 months waiting here, and {warrior.idle_surcharge} silver of back wages on his price" in result


def test_row_names_no_back_wages_without_a_wait():
    html = render_component(
        tag=PUB_ROW_TAG, context={"warrior": _warrior(), "knowledge": WarriorKnowledge.RIVAL, "is_player_faction": True}
    )

    result = _text(html)

    assert "months waiting here" not in result
