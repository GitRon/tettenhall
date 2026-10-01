from apps.warband.skirmish.models.battle_history import BattleHistory
from apps.warband.templatetags.battle_log import casualty_side


def test_casualty_side_of_the_players_own_man():
    result = casualty_side(BattleHistory(faction_id=1), 1)

    assert result == "own"


def test_casualty_side_of_an_enemy():
    result = casualty_side(BattleHistory(faction_id=2), 1)

    assert result == "theirs"


def test_casualty_side_of_a_fight_between_two_rivals():
    result = casualty_side(BattleHistory(faction_id=2), None)

    assert result == "watched"
