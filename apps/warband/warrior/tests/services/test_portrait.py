from unittest import mock

import pytest

from apps.warband.warrior.choices.portrait_kind import PortraitKindChoices
from apps.warband.warrior.models.hair_colour import HairColour
from apps.warband.warrior.models.portrait_piece import PortraitPiece
from apps.warband.warrior.services.portrait import draw_portrait


@pytest.mark.django_db
def test_draw_portrait_takes_every_layer_from_its_own_kind():
    """Every draw takes the first of what it is offered, which is a piece for each of the three layers."""
    with mock.patch("apps.warband.warrior.services.portrait.random.choice", side_effect=lambda options: options[0]):
        result = draw_portrait()

    assert [result["portrait_face"].kind, result["portrait_hair"].kind, result["portrait_beard"].kind] == [
        PortraitKindChoices.KIND_FACE,
        PortraitKindChoices.KIND_HAIR,
        PortraitKindChoices.KIND_BEARD,
    ]


@pytest.mark.django_db
def test_draw_portrait_can_draw_a_bald_and_clean_shaven_man():
    """The last of what each draw is offered is the empty look, so bald and clean-shaven are real draws."""
    with mock.patch("apps.warband.warrior.services.portrait.random.choice", side_effect=lambda options: options[-1]):
        result = draw_portrait()

    assert (result["portrait_hair"], result["portrait_beard"]) == (None, None)


@pytest.mark.django_db
def test_draw_portrait_gives_the_beard_the_colour_of_the_hair():
    with mock.patch("apps.warband.warrior.services.portrait.random.random", return_value=0.99):
        result = draw_portrait()

    assert result["beard_colour"] == result["hair_colour"]


@pytest.mark.django_db
def test_draw_portrait_gives_one_man_in_five_a_beard_of_another_colour():
    with mock.patch("apps.warband.warrior.services.portrait.random.random", return_value=0.0):
        result = draw_portrait()

    assert result["beard_colour"] != result["hair_colour"]


@pytest.mark.django_db
def test_draw_portrait_raises_without_the_reference_data():
    PortraitPiece.objects.all().delete()
    HairColour.objects.all().delete()

    with pytest.raises(RuntimeError, match="portraitpiece haircolour"):
        draw_portrait()
