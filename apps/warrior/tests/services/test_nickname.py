from apps.warrior.services.nickname import (
    BOTH_LOW_NICKNAME,
    DEXTERITY_HIGH_NICKNAME,
    STRENGTH_HIGH_NICKNAME,
    get_nickname,
)


def test_get_nickname_for_strength_above_the_cutoff():
    result = get_nickname(strength=18, dexterity=10, baseline=10, spread=4, minimum=3)

    assert result == STRENGTH_HIGH_NICKNAME


def test_get_nickname_for_dexterity_above_the_cutoff():
    result = get_nickname(strength=10, dexterity=18, baseline=10, spread=4, minimum=3)

    assert result == DEXTERITY_HIGH_NICKNAME


def test_get_nickname_names_only_the_further_of_two_reaches():
    result = get_nickname(strength=18, dexterity=21, baseline=10, spread=4, minimum=3)

    assert result == DEXTERITY_HIGH_NICKNAME


def test_get_nickname_gives_a_dead_heat_to_strength():
    result = get_nickname(strength=18, dexterity=18, baseline=10, spread=4, minimum=3)

    assert result == STRENGTH_HIGH_NICKNAME


def test_get_nickname_for_a_man_at_the_floor_in_both_attributes():
    result = get_nickname(strength=3, dexterity=3, baseline=10, spread=4, minimum=3)

    assert result == BOTH_LOW_NICKNAME


def test_get_nickname_for_a_man_at_the_floor_in_one_attribute_only():
    """
    Being feeble is a position rather than a distance, and one bad attribute is not it - the floor is
    where a quarter of every mercenary's rolls land, so half a heap is no distinction at all.
    """
    result = get_nickname(strength=3, dexterity=11, baseline=10, spread=4, minimum=3)

    assert result is None


def test_get_nickname_for_an_ordinary_man():
    result = get_nickname(strength=13, dexterity=7, baseline=10, spread=4, minimum=3)

    assert result is None


def test_get_nickname_scales_with_the_spread_it_is_given():
    """
    The same roll is exceptional among one archetype and unremarkable among another, which is the
    whole reason the spread travels with the warrior instead of the cut-off being a fixed number.
    """
    result = get_nickname(strength=18, dexterity=10, baseline=10, spread=10, minimum=3)

    assert result is None
