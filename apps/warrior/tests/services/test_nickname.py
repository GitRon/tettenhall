import pytest

from apps.warrior.domain.attribute_draw import AttributeDraw
from apps.warrior.services.nickname import (
    DEXTERITY_FAR_NICKNAMES,
    DEXTERITY_NICKNAMES,
    FLOOR_NICKNAMES,
    HEALTH_FAR_NICKNAMES,
    HEALTH_NICKNAMES,
    MORALE_FAR_NICKNAMES,
    MORALE_NICKNAMES,
    STRENGTH_FAR_NICKNAMES,
    STRENGTH_NICKNAMES,
    get_nickname,
)


@pytest.fixture
def ordinary() -> dict:
    """
    Four attributes each sitting exactly on its own mean, so nothing is earned until a test moves
    one. The near threshold is two spreads out and the far one two and a half, which puts strength
    and dexterity at 18 and 20, health at 30 and 33, morale at 16 and 18.
    """
    return {
        "strength": AttributeDraw(value=10, baseline=10, spread=4),
        "dexterity": AttributeDraw(value=10, baseline=10, spread=4),
        "health": AttributeDraw(value=20, baseline=20, spread=5),
        "morale": AttributeDraw(value=10, baseline=10, spread=3),
        "stats_minimum": 3,
        "variant": 0,
    }


def test_get_nickname_for_strength_past_the_near_threshold(ordinary):
    ordinary["strength"] = AttributeDraw(value=18, baseline=10, spread=4)

    result = get_nickname(**ordinary)

    assert result == STRENGTH_NICKNAMES[0]


def test_get_nickname_for_strength_past_the_far_threshold(ordinary):
    ordinary["strength"] = AttributeDraw(value=20, baseline=10, spread=4)

    result = get_nickname(**ordinary)

    assert result == STRENGTH_FAR_NICKNAMES[0]


def test_get_nickname_for_dexterity_past_the_near_threshold(ordinary):
    ordinary["dexterity"] = AttributeDraw(value=18, baseline=10, spread=4)

    result = get_nickname(**ordinary)

    assert result == DEXTERITY_NICKNAMES[0]


def test_get_nickname_for_dexterity_past_the_far_threshold(ordinary):
    ordinary["dexterity"] = AttributeDraw(value=20, baseline=10, spread=4)

    result = get_nickname(**ordinary)

    assert result == DEXTERITY_FAR_NICKNAMES[0]


def test_get_nickname_for_health_past_the_near_threshold(ordinary):
    ordinary["health"] = AttributeDraw(value=30, baseline=20, spread=5)

    result = get_nickname(**ordinary)

    assert result == HEALTH_NICKNAMES[0]


def test_get_nickname_for_health_past_the_far_threshold(ordinary):
    ordinary["health"] = AttributeDraw(value=33, baseline=20, spread=5)

    result = get_nickname(**ordinary)

    assert result == HEALTH_FAR_NICKNAMES[0]


def test_get_nickname_for_morale_past_the_near_threshold(ordinary):
    ordinary["morale"] = AttributeDraw(value=16, baseline=10, spread=3)

    result = get_nickname(**ordinary)

    assert result == MORALE_NICKNAMES[0]


def test_get_nickname_for_morale_past_the_far_threshold(ordinary):
    ordinary["morale"] = AttributeDraw(value=18, baseline=10, spread=3)

    result = get_nickname(**ordinary)

    assert result == MORALE_FAR_NICKNAMES[0]


def test_get_nickname_names_only_the_attribute_that_reached_furthest(ordinary):
    """
    Strength clears the near threshold and morale clears the far one, so the man is named for his
    nerve rather than his arm.
    """
    ordinary["strength"] = AttributeDraw(value=18, baseline=10, spread=4)
    ordinary["morale"] = AttributeDraw(value=20, baseline=10, spread=3)

    result = get_nickname(**ordinary)

    assert result == MORALE_FAR_NICKNAMES[0]


def test_get_nickname_gives_a_dead_heat_to_the_earlier_attribute(ordinary):
    ordinary["strength"] = AttributeDraw(value=18, baseline=10, spread=4)
    ordinary["dexterity"] = AttributeDraw(value=18, baseline=10, spread=4)

    result = get_nickname(**ordinary)

    assert result == STRENGTH_NICKNAMES[0]


def test_get_nickname_for_a_man_at_the_floor_in_both_stats(ordinary):
    ordinary["strength"] = AttributeDraw(value=3, baseline=10, spread=4)
    ordinary["dexterity"] = AttributeDraw(value=3, baseline=10, spread=4)

    result = get_nickname(**ordinary)

    assert result == FLOOR_NICKNAMES[0]


def test_get_nickname_for_a_man_at_the_floor_in_one_stat_only(ordinary):
    """
    Being feeble is a position rather than a distance, and one bad attribute is not it - the floor is
    where a quarter of every mercenary's rolls land, so half a heap is no distinction at all.
    """
    ordinary["strength"] = AttributeDraw(value=3, baseline=10, spread=4)

    result = get_nickname(**ordinary)

    assert result is None


def test_get_nickname_for_an_ordinary_man(ordinary):
    result = get_nickname(**ordinary)

    assert result is None


def test_get_nickname_phrases_the_state_by_the_warriors_own_variant(ordinary):
    ordinary["strength"] = AttributeDraw(value=18, baseline=10, spread=4)
    ordinary["variant"] = 1

    result = get_nickname(**ordinary)

    assert result == STRENGTH_NICKNAMES[1]


def test_get_nickname_wraps_a_variant_round_the_wordings_it_lands_in(ordinary):
    """
    The bound the variant is drawn from is a common multiple of the wording counts rather than a count
    of its own, so every state has to fold it down to its own length.
    """
    ordinary["strength"] = AttributeDraw(value=3, baseline=10, spread=4)
    ordinary["dexterity"] = AttributeDraw(value=3, baseline=10, spread=4)
    ordinary["variant"] = 3

    result = get_nickname(**ordinary)

    assert result == FLOOR_NICKNAMES[0]
