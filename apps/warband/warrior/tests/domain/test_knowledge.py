from apps.warband.warrior.domain.knowledge import WarriorKnowledge


def test_for_relation_commanded():
    result = WarriorKnowledge.for_relation(is_commanded=True, is_held=False)

    assert result is WarriorKnowledge.COMMANDED


def test_for_relation_held():
    result = WarriorKnowledge.for_relation(is_commanded=False, is_held=True)

    assert result is WarriorKnowledge.HELD


def test_for_relation_rival():
    result = WarriorKnowledge.for_relation(is_commanded=False, is_held=False)

    assert result is WarriorKnowledge.RIVAL


def test_for_relation_commanded_outranks_held():
    """A man cannot be in the war band and in the cells at once, so the generous answer loses."""
    result = WarriorKnowledge.for_relation(is_commanded=True, is_held=True)

    assert result is WarriorKnowledge.COMMANDED


def test_numbers_are_exact_commanded():
    result = WarriorKnowledge.COMMANDED.numbers_are_exact

    assert result is True


def test_numbers_are_exact_held():
    result = WarriorKnowledge.HELD.numbers_are_exact

    assert result is False


def test_numbers_are_exact_rival():
    result = WarriorKnowledge.RIVAL.numbers_are_exact

    assert result is False


def test_gear_is_visible_commanded():
    result = WarriorKnowledge.COMMANDED.gear_is_visible

    assert result is True


def test_gear_is_visible_held():
    result = WarriorKnowledge.HELD.gear_is_visible

    assert result is True


def test_gear_is_visible_rival():
    result = WarriorKnowledge.RIVAL.gear_is_visible

    assert result is False
