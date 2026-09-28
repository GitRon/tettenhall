import re

import pytest

from apps.warband.warrior.models.hair_colour import HairColour


@pytest.mark.django_db
def test_str_is_the_name():
    assert str(HairColour.objects.get(name="Chestnut")) == "Chestnut"


@pytest.mark.django_db
def test_every_shipped_colour_is_a_hex_colour():
    """The value lands in an inline style unchecked, and a malformed one leaves the hair uncoloured grey."""
    malformed = [colour.hex for colour in HairColour.objects.all() if not re.fullmatch(r"#[0-9a-f]{6}", colour.hex)]

    assert malformed == []
