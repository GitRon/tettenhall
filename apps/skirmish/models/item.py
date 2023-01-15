from django.db import models

from apps.core.validators import dice_notation
from apps.skirmish.managers.item import ItemManager
from apps.skirmish.models.faction import Faction


class Item(models.Model):
    class TypeChoices(models.IntegerChoices):
        TYPE_WEAPON = 1, "Weapon"
        TYPE_ARMOR = 2, "Armor"

    type = models.PositiveSmallIntegerField("Type", choices=TypeChoices.choices)
    price = models.PositiveSmallIntegerField("Price")
    value = models.CharField("Value", validators=[dice_notation], max_length=10)
    owner = models.ForeignKey(Faction, verbose_name="Owning faction", on_delete=models.CASCADE)

    objects = ItemManager()

    class Meta:
        verbose_name = "Item"
        verbose_name_plural = "Items"
        default_related_name = "items"

    def __str__(self):
        return f"{self.get_type_display()} ({self.value}, {self.owner})"
