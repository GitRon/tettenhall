from apps.warband.warrior.domain.knowledge import WarriorKnowledge
from apps.warband.warrior.domain.potential import (
    POTENTIAL_A_LITTLE_LEFT,
    POTENTIAL_LEFT,
    POTENTIAL_MUCH_LEFT,
    POTENTIAL_SPENT,
    describe_potential,
)


def test_describe_potential_his_own_man_with_much_left():
    result = describe_potential(levels_left=2, knowledge=WarriorKnowledge.COMMANDED)

    assert result == POTENTIAL_MUCH_LEFT


def test_describe_potential_his_own_man_with_a_little_left():
    result = describe_potential(levels_left=1, knowledge=WarriorKnowledge.COMMANDED)

    assert result == POTENTIAL_A_LITTLE_LEFT


def test_describe_potential_his_own_man_at_his_ceiling():
    result = describe_potential(levels_left=0, knowledge=WarriorKnowledge.COMMANDED)

    assert result == POTENTIAL_SPENT


def test_describe_potential_a_held_man_with_room_left_is_told_only_that_there_is_some():
    """A little and a lot read the same in the pub, so hiring stays a judgement."""
    result = describe_potential(levels_left=1, knowledge=WarriorKnowledge.HELD)

    assert result == POTENTIAL_LEFT


def test_describe_potential_a_held_man_at_his_ceiling():
    result = describe_potential(levels_left=0, knowledge=WarriorKnowledge.HELD)

    assert result == POTENTIAL_SPENT


def test_describe_potential_says_nothing_of_a_rivals_man():
    result = describe_potential(levels_left=2, knowledge=WarriorKnowledge.RIVAL)

    assert result is None
