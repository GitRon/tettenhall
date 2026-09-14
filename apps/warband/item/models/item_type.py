from django.db import models

from apps.common.validators import dice_notation


class ItemType(models.Model):
    class FunctionChoices(models.IntegerChoices):
        FUNCTION_WEAPON = 1, "Weapon"
        FUNCTION_ARMOR = 2, "Armor"

    class TierChoices(models.IntegerChoices):
        """
        The band of standing a type belongs to, which is what an item generator draws its pool from.

        Not a damage ordering: the Spear (3d2, 4.5) sits in the rustic band and outdamages the Short
        sword (2d3, 4.0) beside it. Two bands rather than three, because every band then holds both a
        weapon and a piece of armour and no pool the shipped fixture can produce is ever empty.
        """

        TIER_RUSTIC = 1, "Rustic"
        TIER_FINE = 2, "Fine"

    name = models.CharField("Name", max_length=75)
    function = models.PositiveSmallIntegerField("Function", choices=FunctionChoices.choices)
    base_value = models.CharField("Value", validators=[dice_notation], max_length=10)
    svg_image_name = models.CharField("SVG image name", max_length=50)
    is_fallback = models.BooleanField("Is fallback", default=0)
    # Null for the fallbacks, which stand outside the bands rather than at the bottom of them - and a
    # null satisfies no pool filter even if "is_fallback" were ever dropped from the queryset
    tier = models.PositiveSmallIntegerField("Tier", choices=TierChoices.choices, null=True, blank=True, default=None)

    class Meta:
        verbose_name = "Item type"
        verbose_name_plural = "Item types"
        default_related_name = "item_types"

    def __str__(self) -> str:
        return f"{self.name} ({self.get_function_display()})"
