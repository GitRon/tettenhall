from apps.warrior.services.nickname import (
    DEXTERITY_HIGH_NICKNAME,
    DEXTERITY_LOW_NICKNAME,
    STRENGTH_HIGH_NICKNAME,
    STRENGTH_LOW_NICKNAME,
    get_nickname,
)


def test_get_nickname_for_strength_above_the_cutoff():
    result = get_nickname(strength=16, dexterity=10, baseline=10, spread=4)

    assert result == STRENGTH_HIGH_NICKNAME


def test_get_nickname_for_strength_below_the_cutoff():
    result = get_nickname(strength=4, dexterity=10, baseline=10, spread=4)

    assert result == STRENGTH_LOW_NICKNAME


def test_get_nickname_for_dexterity_above_the_cutoff():
    result = get_nickname(strength=10, dexterity=16, baseline=10, spread=4)

    assert result == DEXTERITY_HIGH_NICKNAME


def test_get_nickname_for_dexterity_below_the_cutoff():
    result = get_nickname(strength=10, dexterity=4, baseline=10, spread=4)

    assert result == DEXTERITY_LOW_NICKNAME


def test_get_nickname_for_an_ordinary_man():
    result = get_nickname(strength=13, dexterity=7, baseline=10, spread=4)

    assert result is None


def test_get_nickname_names_only_the_further_of_two_extremes():
    result = get_nickname(strength=15, dexterity=3, baseline=10, spread=4)

    assert result == DEXTERITY_LOW_NICKNAME


def test_get_nickname_gives_a_dead_heat_to_strength():
    result = get_nickname(strength=16, dexterity=4, baseline=10, spread=4)

    assert result == STRENGTH_HIGH_NICKNAME


def test_get_nickname_scales_with_the_spread_it_is_given():
    """
    The same roll is extreme among one archetype and unremarkable among another, which is the whole
    reason the spread travels with the warrior instead of the cut-off being a fixed number.
    """
    result = get_nickname(strength=16, dexterity=10, baseline=10, spread=10)

    assert result is None
