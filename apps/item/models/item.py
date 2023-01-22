from django.db import models

from apps.core.validators import dice_notation
from apps.faction.models.faction import Faction
from apps.item.managers.item import ItemManager
from apps.item.models.item_type import ItemType


class Item(models.Model):
    type = models.ForeignKey(ItemType, verbose_name="Type", on_delete=models.CASCADE)
    price = models.PositiveSmallIntegerField("Price")
    value = models.CharField("Value", validators=[dice_notation], max_length=10)
    owner = models.ForeignKey(Faction, verbose_name="Owning faction", null=True, blank=True, on_delete=models.CASCADE)

    objects = ItemManager()

    class Meta:
        verbose_name = "Item"
        verbose_name_plural = "Items"
        default_related_name = "items"

    def __str__(self):
        return f"{self.type.name} ({self.value})"

    @property
    def is_weapon(self):
        return self.type.function == ItemType.FunctionChoices.FUNCTION_WEAPON

    @property
    def is_armor(self):
        return self.type.function == ItemType.FunctionChoices.FUNCTION_ARMOR

    @property
    def worn_by(self):
        if self.type.function == ItemType.FunctionChoices.FUNCTION_WEAPON and self.warrior_weapon:
            return self.warrior_weapon
        elif self.type.function == ItemType.FunctionChoices.FUNCTION_ARMOR and self.warrior_armor:
            return self.warrior_armor
