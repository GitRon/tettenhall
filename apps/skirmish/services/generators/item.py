import random

from apps.faction.models.faction import Faction
from apps.skirmish.models.item import Item


class ItemGenerator:
    VALUE_ROLLS_MU = 2
    VALUE_ROLLS_SIGMA = 2
    VALUE_SIDES_MU = 6
    VALUE_SIDES_SIGMA = 3

    faction: Faction
    item_type: int

    def __init__(self, faction: Faction, item_type: int) -> None:
        super().__init__()

        self.faction = faction
        self.item_type = item_type

    def process(self):
        value_rolls = 0
        while value_rolls == 0:
            value_rolls = int(round(max(random.gauss(self.VALUE_ROLLS_MU, self.VALUE_ROLLS_SIGMA), 0)))

        value_sides = 0
        while value_sides == 0:
            value_sides = int(round(max(random.gauss(self.VALUE_SIDES_MU, self.VALUE_SIDES_SIGMA), 0)))

        price = pow(value_rolls * value_sides, 2)

        return Item.objects.create(
            type=self.item_type,
            price=price,
            value=f"{value_rolls}d{value_sides}",
            owner=self.faction,
        )
