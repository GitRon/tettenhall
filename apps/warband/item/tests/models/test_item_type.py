import re

import pytest
from django.conf import settings

from apps.warband.item.models.item_type import ItemType
from apps.warband.item.tests.factories.item_type import ItemTypeFactory

ICON_DIRECTORY = settings.BASE_DIR / "static" / "svg" / "icons"

# The game-icons.net download ships every drawing on top of a black square covering the whole viewBox. The
# icons are painted as a mask, so that square masks in as a solid block with the drawing invisible inside it.
FULL_BLEED_BACKGROUND = re.compile(r'd="M0 0h512v512H0z"|<rect[^>]*width="(100%|512)"')


@pytest.mark.django_db
def test_str_contains_name_and_function():
    item_type = ItemTypeFactory(name="Battle axe", function=ItemType.FunctionChoices.FUNCTION_WEAPON)

    assert str(item_type) == "Battle axe (Weapon)"


@pytest.mark.django_db
def test_every_shipped_item_type_has_an_icon_to_draw():
    """
    A missing file is no error anywhere: the mask resolves to nothing and the card shows an empty square.
    """
    missing = [
        item_type.svg_image_name
        for item_type in ItemType.objects.all()
        if not (ICON_DIRECTORY / f"{item_type.svg_image_name}.svg").is_file()
    ]

    assert missing == []


@pytest.mark.parametrize("icon", sorted(ICON_DIRECTORY.glob("*.svg")), ids=lambda icon: icon.stem)
def test_no_icon_carries_a_background_that_would_mask_in_as_a_square(icon):
    assert FULL_BLEED_BACKGROUND.search(icon.read_text(encoding="utf-8")) is None
