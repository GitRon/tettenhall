import pytest
from django.core.exceptions import ValidationError

from apps.common.validators import dice_notation


def test_dice_notation_accepts_a_dice_string():
    assert dice_notation("2d4") is None


def test_dice_notation_rejects_anything_else():
    with pytest.raises(ValidationError, match="is not a dice notation"):
        dice_notation("two swords")
