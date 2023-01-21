import random

from apps.faction.models.faction import Faction
from apps.item.models.item import Item
from apps.item.models.item_type import ItemType


class ItemGenerator:
    VALUE_ROLLS_MU = 2
    VALUE_ROLLS_SIGMA = 2
    VALUE_SIDES_MU = 6
    VALUE_SIDES_SIGMA = 3

    faction: Faction
    item_type: int

    def __init__(self, faction: Faction | None, item_type: int) -> None:
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

        """
        # todo idee von christian:
        EW von xdy ist x * (y + 1) / 2.
        Dann Preis = x * (y + 1) / 2 * y z.B.
        Das * y am Ende, um Streuung reinzubringen
        """
        price = pow(value_rolls * value_sides, 1.5)

        return Item.objects.create(
            type=ItemType.objects.get(function=self.item_type),
            price=price,
            value=f"{value_rolls}d{value_sides}",
            owner=self.faction,
        )
