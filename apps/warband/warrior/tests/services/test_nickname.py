import pytest

from apps.warband.warrior.domain.attribute_draw import AttributeDraw
from apps.warband.warrior.services.nickname import (
    DEXTERITY_FAR_NICKNAMES,
    DEXTERITY_NICKNAMES,
    HEALTH_FAR_NICKNAMES,
    HEALTH_LOW_NICKNAMES,
    HEALTH_NICKNAMES,
    MORALE_FAR_NICKNAMES,
    MORALE_LOW_NICKNAMES,
    MORALE_NICKNAMES,
    STATS_FLOOR_NICKNAMES,
    STRENGTH_FAR_NICKNAMES,
    STRENGTH_NICKNAMES,
    get_nickname,
)


@pytest.fixture
def ordinary() -> dict:
    """
    Four attributes each sitting exactly on its own mean, so nothing is earned until a test moves one.

    Upwards the near threshold is two spreads out and the far one two and a half, which puts strength
    and dexterity at 18 and 20, health at 30 and 33, morale at 16 and 18. Downwards the cut is 1.75
    spreads, so health falls to the bottom at 11 and morale at 5, and the stats reach their floor at 3.
    """
    return {
        "strength": AttributeDraw(value=10, baseline=10, spread=4, minimum=3),
        "dexterity": AttributeDraw(value=10, baseline=10, spread=4, minimum=3),
        "health": AttributeDraw(value=20, baseline=20, spread=5),
        "morale": AttributeDraw(value=10, baseline=10, spread=3),
        "variant": 0,
    }


def test_get_nickname_for_strength_past_the_near_threshold(ordinary):
    ordinary["strength"] = AttributeDraw(value=18, baseline=10, spread=4, minimum=3)

    result = get_nickname(**ordinary)

    assert result == STRENGTH_NICKNAMES[0]


def test_get_nickname_for_strength_past_the_far_threshold(ordinary):
    ordinary["strength"] = AttributeDraw(value=20, baseline=10, spread=4, minimum=3)

    result = get_nickname(**ordinary)

    assert result == STRENGTH_FAR_NICKNAMES[0]


def test_get_nickname_for_dexterity_past_the_near_threshold(ordinary):
    ordinary["dexterity"] = AttributeDraw(value=18, baseline=10, spread=4, minimum=3)

    result = get_nickname(**ordinary)

    assert result == DEXTERITY_NICKNAMES[0]


def test_get_nickname_for_dexterity_past_the_far_threshold(ordinary):
    ordinary["dexterity"] = AttributeDraw(value=20, baseline=10, spread=4, minimum=3)

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
    ordinary["strength"] = AttributeDraw(value=18, baseline=10, spread=4, minimum=3)
    ordinary["morale"] = AttributeDraw(value=20, baseline=10, spread=3)

    result = get_nickname(**ordinary)

    assert result == MORALE_FAR_NICKNAMES[0]


def test_get_nickname_gives_a_dead_heat_to_the_earlier_attribute(ordinary):
    ordinary["strength"] = AttributeDraw(value=18, baseline=10, spread=4, minimum=3)
    ordinary["dexterity"] = AttributeDraw(value=18, baseline=10, spread=4, minimum=3)

    result = get_nickname(**ordinary)

    assert result == STRENGTH_NICKNAMES[0]


def test_get_nickname_lets_a_good_roll_outrank_a_bad_one(ordinary):
    """
    On the floor in both arms and two spreads above his kind in nerve. What he is exceptional at is
    the more interesting fact, and the unflattering states are the commoner ones.
    """
    ordinary["strength"] = AttributeDraw(value=3, baseline=10, spread=4, minimum=3)
    ordinary["dexterity"] = AttributeDraw(value=3, baseline=10, spread=4, minimum=3)
    ordinary["morale"] = AttributeDraw(value=16, baseline=10, spread=3)

    result = get_nickname(**ordinary)

    assert result == MORALE_NICKNAMES[0]


def test_get_nickname_for_a_man_on_the_floor_in_both_arms(ordinary):
    ordinary["strength"] = AttributeDraw(value=3, baseline=10, spread=4, minimum=3)
    ordinary["dexterity"] = AttributeDraw(value=3, baseline=10, spread=4, minimum=3)

    result = get_nickname(**ordinary)

    assert result == STATS_FLOOR_NICKNAMES[0]


def test_get_nickname_for_a_man_on_the_floor_in_one_arm_only(ordinary):
    """
    A quarter of every mercenary's strength rolls land on the floor, so one arm is no distinction at
    all - which is why the two are read together rather than each carrying an epithet.
    """
    ordinary["strength"] = AttributeDraw(value=3, baseline=10, spread=4, minimum=3)

    result = get_nickname(**ordinary)

    assert result is None


def test_get_nickname_for_a_man_whose_health_fell_to_the_bottom(ordinary):
    ordinary["health"] = AttributeDraw(value=11, baseline=20, spread=5)

    result = get_nickname(**ordinary)

    assert result == HEALTH_LOW_NICKNAMES[0]


def test_get_nickname_for_a_man_whose_nerve_fell_to_the_bottom(ordinary):
    ordinary["morale"] = AttributeDraw(value=5, baseline=10, spread=3)

    result = get_nickname(**ordinary)

    assert result == MORALE_LOW_NICKNAMES[0]


def test_get_nickname_clamps_the_bottom_cut_to_the_floor(ordinary):
    """
    A fyrd man's health is drawn at a mean of ten against a spread of ten, so 1.75 spreads below the
    mean is a negative figure and only the floor is left to fall to.
    """
    ordinary["health"] = AttributeDraw(value=1, baseline=10, spread=10)

    result = get_nickname(**ordinary)

    assert result == HEALTH_LOW_NICKNAMES[0]


def test_get_nickname_leaves_a_wide_spread_short_of_its_own_bottom(ordinary):
    """
    The other side of the clamp: against that same mean of ten and spread of ten, eleven health is an
    ordinary man rather than one point over a cut that sits nowhere.
    """
    ordinary["health"] = AttributeDraw(value=11, baseline=10, spread=10)

    result = get_nickname(**ordinary)

    assert result is None


def test_get_nickname_names_the_arms_ahead_of_a_second_failing(ordinary):
    """
    On the floor in both arms and down at the bottom in health at once. The arms are the completest
    failing - two attributes gone rather than one - so they are what he is called for, whichever of
    the two is rarer for his archetype.
    """
    ordinary["strength"] = AttributeDraw(value=3, baseline=10, spread=4, minimum=3)
    ordinary["dexterity"] = AttributeDraw(value=3, baseline=10, spread=4, minimum=3)
    ordinary["health"] = AttributeDraw(value=11, baseline=20, spread=5)

    result = get_nickname(**ordinary)

    assert result == STATS_FLOOR_NICKNAMES[0]


def test_get_nickname_names_health_ahead_of_nerve(ordinary):
    ordinary["health"] = AttributeDraw(value=11, baseline=20, spread=5)
    ordinary["morale"] = AttributeDraw(value=5, baseline=10, spread=3)

    result = get_nickname(**ordinary)

    assert result == HEALTH_LOW_NICKNAMES[0]


def test_get_nickname_for_an_ordinary_man(ordinary):
    result = get_nickname(**ordinary)

    assert result is None


def test_get_nickname_phrases_the_state_by_the_warriors_own_variant(ordinary):
    ordinary["strength"] = AttributeDraw(value=18, baseline=10, spread=4, minimum=3)
    ordinary["variant"] = 1

    result = get_nickname(**ordinary)

    assert result == STRENGTH_NICKNAMES[1]


def test_get_nickname_wraps_a_variant_round_the_wordings_it_lands_in(ordinary):
    """
    The bound the variant is drawn from is a common multiple of the wording counts rather than a count
    of its own, so every state has to fold it down to its own length.
    """
    ordinary["morale"] = AttributeDraw(value=5, baseline=10, spread=3)
    ordinary["variant"] = 3

    result = get_nickname(**ordinary)

    assert result == MORALE_LOW_NICKNAMES[0]
