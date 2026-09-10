from apps.warband.skirmish.models.battle_history import BattleHistory
from apps.warband.skirmish.projections.battle_log import BattleLog
from apps.warband.skirmish.tests.factories.battle_history import BattleHistoryFactory


def test_from_lines_stacks_the_rounds_newest_first():
    """
    The stack is reversed and the lines inside a round are not, which is the whole of what this
    projection does. Both halves are asserted here because getting either one alone right is no use.
    """
    battle_log = BattleLog.from_lines(
        line_list=[
            BattleHistoryFactory.build(message="first blow"),
            BattleHistoryFactory.build(message="second blow"),
            BattleHistoryFactory.build(kind=BattleHistory.KindChoices.KIND_ROUND_FINISHED),
            BattleHistoryFactory.build(message="third blow"),
            BattleHistoryFactory.build(kind=BattleHistory.KindChoices.KIND_ROUND_FINISHED),
        ]
    )

    assert [log_round.number for log_round in battle_log.round_list] == [2, 1]
    assert [log.message for log in battle_log.round_list[1].line_list] == ["first blow", "second blow"]


def test_from_lines_drops_the_boundary_line_it_cut_at():
    """
    The heading over the block says "Round 1", so the line whose whole content is "Round 1 finished."
    is not rendered underneath it as well.
    """
    battle_log = BattleLog.from_lines(
        line_list=[
            BattleHistoryFactory.build(message="a blow"),
            BattleHistoryFactory.build(message="Round 1 finished.", kind=BattleHistory.KindChoices.KIND_ROUND_FINISHED),
        ]
    )

    assert [log.message for log in battle_log.round_list[0].line_list] == ["a blow"]


def test_from_lines_folds_the_aftermath_into_the_round_that_ended_the_fight():
    """
    The victor, the experience and the loot are written off "SkirmishFinished", downstream of the
    last "RoundFinished" - so they arrive after the final boundary and are not a round nobody fought.
    """
    battle_log = BattleLog.from_lines(
        line_list=[
            BattleHistoryFactory.build(message="a blow"),
            BattleHistoryFactory.build(kind=BattleHistory.KindChoices.KIND_ROUND_FINISHED),
            BattleHistoryFactory.build(message="Skirmish finished. Mercia won."),
        ]
    )

    assert len(battle_log.round_list) == 1
    assert [log.message for log in battle_log.round_list[0].line_list] == ["a blow", "Skirmish finished. Mercia won."]


def test_from_lines_reads_a_log_with_no_boundary_yet_as_the_first_round():
    battle_log = BattleLog.from_lines(line_list=[BattleHistoryFactory.build(message="a blow")])

    assert [log_round.number for log_round in battle_log.round_list] == [1]
    assert [log.message for log in battle_log.round_list[0].line_list] == ["a blow"]


def test_from_lines_holds_no_round_for_a_fight_nobody_has_started():
    battle_log = BattleLog.from_lines(line_list=[])

    assert battle_log.round_list == []
