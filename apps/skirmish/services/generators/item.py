import random

from apps.core.domain.random import DiceNotation
from apps.faction.models.faction import Faction
from apps.item.models.item import Item
from apps.item.models.item_type import ItemType


class ItemGenerator:
    MODIFIER_ROLLS_MU = 2
    MODIFIER_ROLLS_SIGMA = 2

    faction: Faction
    item_type: int

    def __init__(self, faction: Faction | None, item_type: int) -> None:
        super().__init__()

        self.faction = faction
        self.item_type = item_type

    def _determine_condition(self, modifier: int) -> int:
        if modifier < self.MODIFIER_ROLLS_MU - self.MODIFIER_ROLLS_SIGMA:
            return Item.ConditionChoices.CONDITION_RUSTY
        elif self.MODIFIER_ROLLS_MU - self.MODIFIER_ROLLS_SIGMA <= modifier < self.MODIFIER_ROLLS_MU:
            return Item.ConditionChoices.CONDITION_CHEAP
        elif self.MODIFIER_ROLLS_MU <= modifier < self.MODIFIER_ROLLS_MU + self.MODIFIER_ROLLS_SIGMA:
            return Item.ConditionChoices.CONDITION_TRADITIONAL
        elif modifier >= self.MODIFIER_ROLLS_MU - self.MODIFIER_ROLLS_SIGMA:
            return Item.ConditionChoices.CONDITION_SUPERIOR
        else:
            raise RuntimeError("Invalid condition")

    def process(self):
        # Modifier can be negative, DiceNotation class takes care of not dealing negative damage
        modifier = int(round(random.gauss(self.MODIFIER_ROLLS_MU, self.MODIFIER_ROLLS_SIGMA)))

        item_type = ItemType.objects.filter(function=self.item_type).exclude(is_fallback=True).order_by("?").first()

        dice_notation = DiceNotation(dice_string=item_type.base_value, modifier=modifier)
        price = dice_notation.expectancy_value * dice_notation.sides * max(modifier, 1)

        return Item.objects.create(
            type=item_type,
            condition=self._determine_condition(modifier=modifier),
            price=price,
            modifier=modifier,
            owner=self.faction,
        )
