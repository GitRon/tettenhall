from django.db import models

from apps.warband.warrior.choices.portrait_kind import PortraitKindChoices


class PortraitPieceQuerySet(models.QuerySet):
    def of_kind(self, *, kind: str) -> PortraitPieceQuerySet:
        return self.filter(kind=kind)


class PortraitPiece(models.Model):
    """
    One layer a warrior's portrait is stacked from: a bare face, a hairstyle or a beard.

    Reference data, a fixture at the app root, so the catalogue grows without a migration - see
    docs/patterns/portraits.md for the layer contract a new piece has to meet.

    Where a layer sits is stored on the piece rather than computed, as fractions of the face canvas: the
    pieces were cut from one contact sheet at differing scales, and a chin beard and a braided one hold a
    different share of their own sprite above the jaw, so no single rule seats them all. A face covers the
    whole canvas, which is what it is measured against.
    """

    kind = models.CharField("Kind", choices=PortraitKindChoices.choices, max_length=10)
    number = models.PositiveSmallIntegerField("Number")
    # A path for the "static" tag, not a file field: the pieces ship with the code, nobody uploads one
    image = models.CharField("Image", max_length=100)
    left = models.DecimalField("Left", max_digits=5, decimal_places=4, default=0)
    top = models.DecimalField("Top", max_digits=5, decimal_places=4, default=0)
    width = models.DecimalField("Width", max_digits=5, decimal_places=4, default=1)

    objects = PortraitPieceQuerySet.as_manager()

    class Meta:
        verbose_name = "Portrait piece"
        verbose_name_plural = "Portrait pieces"
        default_related_name = "portrait_pieces"
        ordering = ("kind", "number")
        constraints = (models.UniqueConstraint(fields=("kind", "number"), name="unique_portrait_piece_number"),)

    def __str__(self) -> str:
        return f"{self.get_kind_display()} {self.number:02d}"
