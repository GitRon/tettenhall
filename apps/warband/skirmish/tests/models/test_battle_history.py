from apps.warband.skirmish.models import BattleHistory
from apps.warband.skirmish.tests.factories.battle_history import BattleHistoryFactory


def test_str_returns_the_message():
    battle_history = BattleHistoryFactory.build(message="Round 1 finished.")

    assert str(battle_history) == "Round 1 finished."


def test_is_casualty_marks_a_line_about_a_man_going_down():
    battle_history = BattleHistoryFactory.build(kind=BattleHistory.KindChoices.KIND_WARRIOR_KILLED)

    assert battle_history.is_casualty is True


def test_is_casualty_leaves_the_blow_by_blow_alone():
    battle_history = BattleHistoryFactory.build(kind=BattleHistory.KindChoices.KIND_NARRATION)

    assert battle_history.is_casualty is False


def test_icon_names_the_mark_for_the_kind():
    battle_history = BattleHistoryFactory.build(kind=BattleHistory.KindChoices.KIND_WARRIOR_LEFT_THE_FIELD)

    assert battle_history.icon == "fa-person-running"


def test_every_way_off_the_field_has_a_mark():
    """
    The three kinds that take a man out of the fight are exactly the ones the panel marks, so a
    fourth added to the choices has to say whether it is one of them rather than pick up silence.
    """
    marked_kinds = set(BattleHistory.KIND_ICONS)

    assert marked_kinds == {
        BattleHistory.KindChoices.KIND_WARRIOR_KILLED,
        BattleHistory.KindChoices.KIND_WARRIOR_INCAPACITATED,
        BattleHistory.KindChoices.KIND_WARRIOR_LEFT_THE_FIELD,
    }
