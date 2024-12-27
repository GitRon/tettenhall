import random

from django.db.models import QuerySet

from apps.core.domain.random import DiceNotation
from apps.faction.models.faction import Faction
from apps.item.models.item import Item
from apps.item.models.item_type import ItemType


class BaseItemGenerator:
    MODIFIER_ROLLS_MU = 2
    MODIFIER_ROLLS_SIGMA = 2

    faction: Faction
    function: int

    def __init__(self, *, faction: Faction | None, item_function: int) -> None:
        super().__init__()

        self.faction = faction
        self.function = item_function

    def _determine_condition(self, *, modifier: int) -> int:
        if modifier < self.MODIFIER_ROLLS_MU - self.MODIFIER_ROLLS_SIGMA:
            return Item.ConditionChoices.CONDITION_RUSTY
        if self.MODIFIER_ROLLS_MU - self.MODIFIER_ROLLS_SIGMA <= modifier < self.MODIFIER_ROLLS_MU:
            return Item.ConditionChoices.CONDITION_CHEAP
        if self.MODIFIER_ROLLS_MU <= modifier < self.MODIFIER_ROLLS_MU + self.MODIFIER_ROLLS_SIGMA:
            return Item.ConditionChoices.CONDITION_TRADITIONAL
        if modifier >= self.MODIFIER_ROLLS_MU - self.MODIFIER_ROLLS_SIGMA:
            return Item.ConditionChoices.CONDITION_SUPERIOR
        raise RuntimeError("Invalid condition")

    def _get_queryset_for_type(self) -> QuerySet:
        return ItemType.objects.filter(function=self.function).exclude(is_fallback=True).order_by("?")

    def process(self) -> Item:
        # Modifier can be negative, DiceNotation class takes care of not dealing negative damage
        modifier = int(round(random.gauss(self.MODIFIER_ROLLS_MU, self.MODIFIER_ROLLS_SIGMA)))

        item_type = self._get_queryset_for_type().first()

        dice_notation = DiceNotation(dice_string=item_type.base_value, modifier=modifier)
        price = dice_notation.expectancy_value * dice_notation.sides * max(modifier, 1)

        return Item.objects.create(
            type=item_type,
            condition=self._determine_condition(modifier=modifier),
            price=price,
            modifier=modifier,
            owner=self.faction,
        )
