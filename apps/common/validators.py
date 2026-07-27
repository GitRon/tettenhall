import re

from django.core.exceptions import ValidationError


# Django calls field validators positionally, so a keyword-only signature would raise a TypeError
# instead of ever validating anything
def dice_notation(value):  # noqa: PBR001
    r"""
    Validates the input to be in the format of "\dd\d", like "2d5".
    """
    match = re.search(r"^\d+d\d+$", value)

    if not match:
        raise ValidationError(
            '"%(value)s" is not a dice notation',
            params={"value": value},
        )
