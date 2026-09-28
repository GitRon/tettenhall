from django.db import models


class HairColour(models.Model):
    """
    A colour a man's hair or beard can be, multiplied over the greyscale layer at render time.

    Reference data beside the pieces it colours, and the one colour in the project that is not a token in
    the stylesheet's theme: it is pigment for a painting, not a colour of the interface - see
    docs/patterns/visual-identity.md.
    """

    name = models.CharField("Name", max_length=30)
    hex = models.CharField("Hex", max_length=7)

    class Meta:
        verbose_name = "Hair colour"
        verbose_name_plural = "Hair colours"
        default_related_name = "hair_colours"
        ordering = ("id",)

    def __str__(self) -> str:
        return self.name
