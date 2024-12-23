import itertools
import random
import re
from dataclasses import dataclass


@dataclass(kw_only=True)
class DiceNotation:
    """
    Dice notation format: "2d4+7"
    Rolls 2 times a die with 4 sides and add 7.
    "2d4" is part of the item type, the modifier comes from the item itself.
    """

    rolls: int
    sides: int
    modifier: int

    def __init__(self, dice_string: str, modifier: int = 0):
        match = re.search(r"^(\d+)d(\d+)$", dice_string)
        self.rolls = int(match[1])
        self.sides = int(match[2])
        self.modifier = modifier

    def __str__(self):
        return f"{self.rolls}d{self.sides}"

    @property
    def result(self) -> int:
        result = 0
        for _ in itertools.repeat(None, self.rolls):
            result += random.randint(1, self.sides)
        return max(result + self.modifier, 0)

    @property
    def expectancy_value(self) -> float:
        return (self.rolls * (self.sides + 1) / 2) + self.modifier
