import pytest

from apps.warband.warrior.choices.nickname import NicknameStateChoices
from apps.warband.warrior.domain.attribute_draw import AttributeDraw
from apps.warband.warrior.services.nickname import (
    MORALE_LOW_NICKNAMES,
    NICKNAME_WORDINGS,
    STRENGTH_NICKNAMES,
    draw_nickname_state,
    resolve_nickname,
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
    }


def test_draw_nickname_state_for_strength_past_the_near_threshold(ordinary):
    ordinary["strength"] = AttributeDraw(value=18, baseline=10, spread=4, minimum=3)

    result = draw_nickname_state(**ordinary)

    assert result == NicknameStateChoices.STRENGTH


def test_draw_nickname_state_for_strength_past_the_far_threshold(ordinary):
    ordinary["strength"] = AttributeDraw(value=20, baseline=10, spread=4, minimum=3)

    result = draw_nickname_state(**ordinary)

    assert result == NicknameStateChoices.STRENGTH_FAR


def test_draw_nickname_state_for_dexterity_past_the_near_threshold(ordinary):
    ordinary["dexterity"] = AttributeDraw(value=18, baseline=10, spread=4, minimum=3)

    result = draw_nickname_state(**ordinary)

    assert result == NicknameStateChoices.DEXTERITY


def test_draw_nickname_state_for_dexterity_past_the_far_threshold(ordinary):
    ordinary["dexterity"] = AttributeDraw(value=20, baseline=10, spread=4, minimum=3)

    result = draw_nickname_state(**ordinary)

    assert result == NicknameStateChoices.DEXTERITY_FAR


def test_draw_nickname_state_for_health_past_the_near_threshold(ordinary):
    ordinary["health"] = AttributeDraw(value=30, baseline=20, spread=5)

    result = draw_nickname_state(**ordinary)

    assert result == NicknameStateChoices.HEALTH


def test_draw_nickname_state_for_health_past_the_far_threshold(ordinary):
    ordinary["health"] = AttributeDraw(value=33, baseline=20, spread=5)

    result = draw_nickname_state(**ordinary)

    assert result == NicknameStateChoices.HEALTH_FAR


def test_draw_nickname_state_for_morale_past_the_near_threshold(ordinary):
    ordinary["morale"] = AttributeDraw(value=16, baseline=10, spread=3)

    result = draw_nickname_state(**ordinary)

    assert result == NicknameStateChoices.MORALE


def test_draw_nickname_state_for_morale_past_the_far_threshold(ordinary):
    ordinary["morale"] = AttributeDraw(value=18, baseline=10, spread=3)

    result = draw_nickname_state(**ordinary)

    assert result == NicknameStateChoices.MORALE_FAR


def test_draw_nickname_state_names_only_the_attribute_that_reached_furthest(ordinary):
    """
    Strength clears the near threshold and morale clears the far one, so the man is named for his
    nerve rather than his arm.
    """
    ordinary["strength"] = AttributeDraw(value=18, baseline=10, spread=4, minimum=3)
    ordinary["morale"] = AttributeDraw(value=20, baseline=10, spread=3)

    result = draw_nickname_state(**ordinary)

    assert result == NicknameStateChoices.MORALE_FAR


def test_draw_nickname_state_gives_a_dead_heat_to_the_earlier_attribute(ordinary):
    ordinary["strength"] = AttributeDraw(value=18, baseline=10, spread=4, minimum=3)
    ordinary["dexterity"] = AttributeDraw(value=18, baseline=10, spread=4, minimum=3)

    result = draw_nickname_state(**ordinary)

    assert result == NicknameStateChoices.STRENGTH


def test_draw_nickname_state_lets_a_good_roll_outrank_a_bad_one(ordinary):
    """
    On the floor in both arms and two spreads above his kind in nerve. What he is exceptional at is
    the more interesting fact, and the unflattering states are the commoner ones.
    """
    ordinary["strength"] = AttributeDraw(value=3, baseline=10, spread=4, minimum=3)
    ordinary["dexterity"] = AttributeDraw(value=3, baseline=10, spread=4, minimum=3)
    ordinary["morale"] = AttributeDraw(value=16, baseline=10, spread=3)

    result = draw_nickname_state(**ordinary)

    assert result == NicknameStateChoices.MORALE


def test_draw_nickname_state_for_a_man_on_the_floor_in_both_arms(ordinary):
    ordinary["strength"] = AttributeDraw(value=3, baseline=10, spread=4, minimum=3)
    ordinary["dexterity"] = AttributeDraw(value=3, baseline=10, spread=4, minimum=3)

    result = draw_nickname_state(**ordinary)

    assert result == NicknameStateChoices.STATS_AT_FLOOR


def test_draw_nickname_state_for_a_man_on_the_floor_in_one_arm_only(ordinary):
    """
    A quarter of every mercenary's strength rolls land on the floor, so one arm is no distinction at
    all - which is why the two are read together rather than each carrying an epithet.
    """
    ordinary["strength"] = AttributeDraw(value=3, baseline=10, spread=4, minimum=3)

    result = draw_nickname_state(**ordinary)

    assert result is None


def test_draw_nickname_state_for_a_man_whose_health_fell_to_the_bottom(ordinary):
    ordinary["health"] = AttributeDraw(value=11, baseline=20, spread=5)

    result = draw_nickname_state(**ordinary)

    assert result == NicknameStateChoices.HEALTH_AT_BOTTOM


def test_draw_nickname_state_for_a_man_whose_nerve_fell_to_the_bottom(ordinary):
    ordinary["morale"] = AttributeDraw(value=5, baseline=10, spread=3)

    result = draw_nickname_state(**ordinary)

    assert result == NicknameStateChoices.MORALE_AT_BOTTOM


def test_draw_nickname_state_clamps_the_bottom_cut_to_the_floor(ordinary):
    """
    A fyrd man's health is drawn at a mean of ten against a spread of ten, so 1.75 spreads below the
    mean is a negative figure and only the floor is left to fall to.
    """
    ordinary["health"] = AttributeDraw(value=1, baseline=10, spread=10)

    result = draw_nickname_state(**ordinary)

    assert result == NicknameStateChoices.HEALTH_AT_BOTTOM


def test_draw_nickname_state_leaves_a_wide_spread_short_of_its_own_bottom(ordinary):
    """
    The other side of the clamp: against that same mean of ten and spread of ten, eleven health is an
    ordinary man rather than one point over a cut that sits nowhere.
    """
    ordinary["health"] = AttributeDraw(value=11, baseline=10, spread=10)

    result = draw_nickname_state(**ordinary)

    assert result is None


def test_draw_nickname_state_names_the_arms_ahead_of_a_second_failing(ordinary):
    """
    On the floor in both arms and down at the bottom in health at once. The arms are the completest
    failing - two attributes gone rather than one - so they are what he is called for, whichever of
    the two is rarer for his archetype.
    """
    ordinary["strength"] = AttributeDraw(value=3, baseline=10, spread=4, minimum=3)
    ordinary["dexterity"] = AttributeDraw(value=3, baseline=10, spread=4, minimum=3)
    ordinary["health"] = AttributeDraw(value=11, baseline=20, spread=5)

    result = draw_nickname_state(**ordinary)

    assert result == NicknameStateChoices.STATS_AT_FLOOR


def test_draw_nickname_state_names_health_ahead_of_nerve(ordinary):
    ordinary["health"] = AttributeDraw(value=11, baseline=20, spread=5)
    ordinary["morale"] = AttributeDraw(value=5, baseline=10, spread=3)

    result = draw_nickname_state(**ordinary)

    assert result == NicknameStateChoices.HEALTH_AT_BOTTOM


def test_draw_nickname_state_for_an_ordinary_man(ordinary):
    result = draw_nickname_state(**ordinary)

    assert result is None


def test_resolve_nickname_phrases_the_state_by_the_warriors_own_variant():
    result = resolve_nickname(state=NicknameStateChoices.STRENGTH, variant=1)

    assert result == STRENGTH_NICKNAMES[1]


def test_resolve_nickname_wraps_a_variant_round_the_wordings_it_lands_in():
    """
    The bound the variant is drawn from is a common multiple of the wording counts rather than a count
    of its own, so every state has to fold it down to its own length.
    """
    result = resolve_nickname(state=NicknameStateChoices.MORALE_AT_BOTTOM, variant=3)

    assert result == MORALE_LOW_NICKNAMES[0]


def test_every_state_has_a_wording():
    """
    A state with no entry is a man the game can stamp and then cannot name - a "KeyError" the moment
    anything renders him, and nothing before that says so.
    """
    assert set(NICKNAME_WORDINGS) == set(NicknameStateChoices)
