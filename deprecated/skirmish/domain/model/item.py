import random

from apps.skirmish.domain.model.random import DiceNotation


class Item:
    TYPE_WEAPON = "weapon"
    TYPE_ARMOR = "armor"

    type: str
    price: int
    value: DiceNotation

    def __init__(self, item_type: str) -> None:
        self.type = item_type
        self.price = random.randrange(1, 100)
        self.value = DiceNotation(rolls=random.randrange(1, 6), sides=random.randrange(2, 20))

    def __str__(self) -> str:
        return f"Item {self.type} ({self.value}, {self.price} Gold)"
