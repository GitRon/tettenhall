from unittest import mock

from apps.common.domain.dice import DiceNotation, DiceRoll


def test_str_leaves_out_the_modifier():
    dice_notation = DiceNotation(dice_string="2d4", modifier=7)

    assert str(dice_notation) == "2d4"


def test_result_sums_up_every_roll_and_the_modifier():
    dice_notation = DiceNotation(dice_string="2d4", modifier=7)

    # Patched at the boundary: the die itself
    with mock.patch("apps.common.domain.dice.random.randint", return_value=3):
        result = dice_notation.result

    assert result == 13


def test_result_never_drops_below_zero():
    dice_notation = DiceNotation(dice_string="1d4", modifier=-10)

    with mock.patch("apps.common.domain.dice.random.randint", return_value=3):
        result = dice_notation.result

    assert result == 0


def test_expectancy_value_averages_the_rolls():
    dice_notation = DiceNotation(dice_string="2d4", modifier=7)

    assert dice_notation.expectancy_value == 12


def test_best_possible_roll_ignores_the_modifier():
    dice_notation = DiceNotation(dice_string="3d5", modifier=-99)

    assert dice_notation.best_possible_roll == 15


def test_best_possible_result_counts_the_modifier_in():
    dice_notation = DiceNotation(dice_string="3d5", modifier=4)

    assert dice_notation.best_possible_result == 19


def test_best_possible_result_never_drops_below_zero():
    """
    The same floor "result" has, so a notation whose modifier is deeper than its dice has a ceiling
    of nothing rather than a negative one nothing could ever be measured against.
    """
    dice_notation = DiceNotation(dice_string="1d4", modifier=-10)

    assert dice_notation.best_possible_result == 0


def test_roll_keeps_the_notation_next_to_the_number():
    dice_notation = DiceNotation(dice_string="2d4", modifier=7)

    with mock.patch("apps.common.domain.dice.random.randint", return_value=3):
        result = dice_notation.roll()

    assert result == DiceRoll(notation=dice_notation, result=13)


def test_is_maximum_for_every_die_on_its_top_face():
    dice_notation = DiceNotation(dice_string="2d4", modifier=7)

    result = DiceRoll(notation=dice_notation, result=15)

    assert result.is_maximum is True


def test_is_maximum_for_a_throw_short_of_the_ceiling():
    dice_notation = DiceNotation(dice_string="2d4", modifier=7)

    result = DiceRoll(notation=dice_notation, result=14)

    assert result.is_maximum is False
