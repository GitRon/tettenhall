from apps.warband.skirmish.tests.factories.warrior import WarriorFactory
from apps.warband.templatetags.potential import experience_threshold, potential_reading
from apps.warband.warrior.domain.knowledge import WarriorKnowledge
from apps.warband.warrior.domain.potential import POTENTIAL_SPENT


def test_potential_reading_gives_the_word():
    result = potential_reading(0, WarriorKnowledge.COMMANDED)

    assert result == POTENTIAL_SPENT


def test_potential_reading_is_empty_where_nothing_is_said():
    result = potential_reading(2, WarriorKnowledge.RIVAL)

    assert result == ""


def test_experience_threshold_for_his_own_man_at_his_ceiling_is_none():
    warrior = WarriorFactory.build(experience=100, potential=2)

    result = experience_threshold(warrior, WarriorKnowledge.COMMANDED)

    assert result is None


def test_experience_threshold_for_a_rivals_man_at_his_ceiling_gives_nothing_away():
    """A threshold that vanished at the ceiling would tell the player a ceiling he is not to know."""
    warrior = WarriorFactory.build(experience=100, potential=2)

    result = experience_threshold(warrior, WarriorKnowledge.RIVAL)

    assert result == 400
