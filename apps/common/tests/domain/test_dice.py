from unittest import mock

from apps.common.domain.dice import DiceNotation


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
