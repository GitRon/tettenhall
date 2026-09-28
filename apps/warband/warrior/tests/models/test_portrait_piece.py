import pytest
from django.contrib.staticfiles import finders

from apps.warband.warrior.choices.portrait_kind import PortraitKindChoices
from apps.warband.warrior.models.portrait_piece import PortraitPiece


@pytest.mark.django_db
def test_str_names_the_kind_and_the_number():
    piece = PortraitPiece.objects.get(kind=PortraitKindChoices.KIND_BEARD, number=3)

    assert str(piece) == "Beard 03"


@pytest.mark.django_db
def test_of_kind_is_the_pieces_of_that_kind():
    assert set(PortraitPiece.objects.of_kind(kind=PortraitKindChoices.KIND_HAIR).values_list("kind", flat=True)) == {
        PortraitKindChoices.KIND_HAIR
    }


@pytest.mark.django_db
def test_every_shipped_piece_has_its_image():
    """A row pointing at a missing file renders a broken layer on every man drawn with it."""
    missing = [piece.image for piece in PortraitPiece.objects.all() if finders.find(piece.image) is None]

    assert missing == []


@pytest.mark.django_db
def test_every_shipped_face_is_the_whole_canvas():
    """The hair and beard fractions are measured against the face, so a face that moved would move them all."""
    faces = PortraitPiece.objects.of_kind(kind=PortraitKindChoices.KIND_FACE)

    assert set(faces.values_list("left", "top", "width")) == {(0, 0, 1)}
