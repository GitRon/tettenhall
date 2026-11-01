from apps.warband.templatetags.potential import potential_reading
from apps.warband.warrior.domain.knowledge import WarriorKnowledge
from apps.warband.warrior.domain.potential import POTENTIAL_SPENT


def test_potential_reading_gives_the_word():
    result = potential_reading(0, WarriorKnowledge.COMMANDED)

    assert result == POTENTIAL_SPENT


def test_potential_reading_is_empty_where_nothing_is_said():
    result = potential_reading(2, WarriorKnowledge.RIVAL)

    assert result == ""
