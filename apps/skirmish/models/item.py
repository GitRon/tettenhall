from django.db import models

from apps.core.validators import dice_notation
from apps.faction.models.faction import Faction
from apps.skirmish.managers.item import ItemManager


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

    @property
    def is_weapon(self):
        return self.type == self.TypeChoices.TYPE_WEAPON

    @property
    def is_armor(self):
        return self.type == self.TypeChoices.TYPE_ARMOR

    @property
    def worn_by(self):
        if self.type == self.TypeChoices.TYPE_WEAPON and self.warrior_weapon:
            return self.warrior_weapon
        elif self.type == self.TypeChoices.TYPE_ARMOR and self.warrior_armor:
            return self.warrior_armor
