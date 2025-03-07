from django.db import models

from apps.common.validators import dice_notation


class ItemType(models.Model):
    class FunctionChoices(models.IntegerChoices):
        FUNCTION_WEAPON = 1, "Weapon"
        FUNCTION_ARMOR = 2, "Armor"

    name = models.CharField("Name", max_length=75)
    function = models.PositiveSmallIntegerField("Function", choices=FunctionChoices.choices)
    base_value = models.CharField("Value", validators=[dice_notation], max_length=10)
    svg_image_name = models.CharField("SVG image name", max_length=50)
    is_fallback = models.BooleanField("Is fallback", default=0)

    class Meta:
        verbose_name = "Item type"
        verbose_name_plural = "Item types"
        default_related_name = "item_types"

    def __str__(self) -> str:
        return f"{self.name} ({self.get_function_display()})"
