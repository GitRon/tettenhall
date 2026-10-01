from apps.common.tests.html import parse, render_component
from apps.warband.skirmish.models.battle_history import BattleHistory

LOG_LINE_TAG = '<c-skirmish.log-line :log="log" :text="text" :player_faction_id="player_faction_id" />'


def test_log_line_marks_a_casualty_with_its_icon():
    log = BattleHistory(kind=BattleHistory.KindChoices.KIND_WARRIOR_KILLED, faction_id=1)

    html = render_component(tag=LOG_LINE_TAG, context={"log": log, "text": "Wulfstan falls", "player_faction_id": 1})

    result = (parse(html).find("i")["class"], parse(html).find("strong").get_text(strip=True))

    assert result == (["fa-solid", BattleHistory.KIND_ICONS[log.kind]], "Wulfstan falls")


def test_log_line_leaves_an_ordinary_line_plain():
    log = BattleHistory(kind=BattleHistory.KindChoices.KIND_NARRATION, faction_id=1)

    html = render_component(tag=LOG_LINE_TAG, context={"log": log, "text": "Sven swings", "player_faction_id": 1})

    result = (parse(html).get_text(strip=True), parse(html).find("strong"))

    assert result == ("Sven swings", None)
