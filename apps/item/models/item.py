from django.db import models

from apps.core.domain.random import DiceNotation
from apps.faction.models.faction import Faction
from apps.item.managers.item import ItemManager
from apps.item.models.item_type import ItemType


class Item(models.Model):
    class ConditionChoices(models.IntegerChoices):
        CONDITION_RUSTY = 1, "Rusty"
        CONDITION_CHEAP = 2, "Cheap"
        CONDITION_TRADITIONAL = 3, "Traditional"
        CONDITION_SUPERIOR = 4, "Superior"

    condition = models.PositiveSmallIntegerField(
        "Condition", choices=ConditionChoices.choices, default=ConditionChoices.CONDITION_TRADITIONAL
    )
    type = models.ForeignKey(ItemType, verbose_name="Type", on_delete=models.CASCADE)
    price = models.PositiveSmallIntegerField("Price")
    modifier = models.SmallIntegerField("Modifier", default=0, help_text='2d4+7 - this is the "7"')
    owner = models.ForeignKey(Faction, verbose_name="Owning faction", null=True, blank=True, on_delete=models.CASCADE)

    objects = ItemManager()

    class Meta:
        verbose_name = "Item"
        verbose_name_plural = "Items"
        default_related_name = "items"

    def __str__(self):
        return f"{self.display_name} ({self.type.base_value}{self.get_modifier_as_string()})"

    @property
    def display_name(self):
        if self.type.is_fallback:
            return f"{self.type.name}"
        return f"{self.get_condition_display()} {self.type.name}"

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
        if self.type.function == ItemType.FunctionChoices.FUNCTION_ARMOR and self.warrior_armor:
            return self.warrior_armor

        return None

    @property
    def expectancy_value(self) -> float:
        return DiceNotation(dice_string=self.type.base_value, modifier=self.modifier).expectancy_value

    def get_modifier_as_string(self):
        return f"+{self.modifier}" if self.modifier >= 0 else f"{self.modifier}"
