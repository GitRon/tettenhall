import itertools
import random
import re
from dataclasses import dataclass


@dataclass
class DiceNotation:
    rolls: int
    sides: int

    def __init__(self, dice_string: str):
        match = re.search(r"^(\d+)d(\d+)$", dice_string)
        self.rolls = int(match[1])
        self.sides = int(match[2])

    def __str__(self):
        return f"{self.rolls}d{self.sides}"

    @property
    def result(self) -> int:
        result = 0
        for _ in itertools.repeat(None, self.rolls):
            result += random.randint(1, self.sides)
        return result
