from django.db import models


class ItemType(models.Model):
    class FunctionChoices(models.IntegerChoices):
        FUNCTION_WEAPON = 1, "Weapon"
        FUNCTION_ARMOR = 2, "Armor"

    function = models.PositiveSmallIntegerField("Function", choices=FunctionChoices.choices, unique=True)
    svg_image_name = models.CharField("SVG image name", max_length=50)

    class Meta:
        verbose_name = "Item type"
        verbose_name_plural = "Item types"
        default_related_name = "item_types"

    def __str__(self):
        return self.get_function_display()
